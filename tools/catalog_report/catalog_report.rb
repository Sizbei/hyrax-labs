#!/usr/bin/env ruby
# frozen_string_literal: true

# catalog_report -- summarize a Hyrax ingestion-pipeline catalog dump.
#
# The pipeline emits a JSON array of material records, each shaped like:
#   {
#     "material_id":     "mat_0001",
#     "supplier":        "ambientcg",
#     "name":            "Brick Wall 01",
#     "slug":            "brick-wall-01",
#     "category":        "brick",
#     "resolution_px":   2048,
#     "physical_size_cm": [100, 100],
#     "textures": [
#       { "map_type": "albedo", "url": "...", "original_label": "Color" },
#       ...
#     ]
#   }
#
# This script reads such a file (or stdin) and prints a summary report:
#   counts by category, counts by supplier, average resolution, and map-type
#   coverage (how many materials include each PBR map type).
#
# Pure Ruby stdlib (json). No external gems.
#
# Usage:
#   ruby catalog_report.rb catalog.json
#   cat catalog.json | ruby catalog_report.rb

require 'json'

module CatalogReport
  # Canonical PBR map types we track coverage for, in display order.
  MAP_TYPES = %w[albedo normal roughness metallic ao height].freeze

  module_function

  # Parse + validate the catalog payload. Raises ArgumentError on bad input so
  # callers can fail fast with a clear message (validate at the boundary).
  def parse(raw)
    data = JSON.parse(raw)
    raise ArgumentError, 'catalog must be a JSON array of records' unless data.is_a?(Array)

    data.each_with_index do |rec, i|
      raise ArgumentError, "record #{i} is not an object" unless rec.is_a?(Hash)
    end
    data
  end

  # Build a structured summary hash from the parsed records.
  def summarize(records)
    by_category = Hash.new(0)
    by_supplier = Hash.new(0)
    resolutions = []
    map_coverage = Hash.new(0)

    records.each do |rec|
      by_category[rec['category'] || '(uncategorized)'] += 1
      by_supplier[rec['supplier'] || '(unknown)'] += 1

      res = rec['resolution_px']
      resolutions << res if res.is_a?(Numeric)

      # A material "covers" a map type if any of its textures has that map_type.
      present = Array(rec['textures'])
                .select { |t| t.is_a?(Hash) }
                .map { |t| t['map_type'] }
                .compact
                .uniq
      present.each { |mt| map_coverage[mt] += 1 }
    end

    avg_res = resolutions.empty? ? 0 : (resolutions.sum.to_f / resolutions.size)

    {
      total: records.size,
      by_category: by_category,
      by_supplier: by_supplier,
      avg_resolution: avg_res,
      resolution_samples: resolutions.size,
      map_coverage: map_coverage
    }
  end

  # Render the summary as a human-readable text report (returns a String).
  def render(summary)
    lines = []
    lines << '=== Hyrax Catalog Report ==='
    lines << "Total materials: #{summary[:total]}"
    lines << ''

    lines << 'By category:'
    lines.concat(format_counts(summary[:by_category], summary[:total]))
    lines << ''

    lines << 'By supplier:'
    lines.concat(format_counts(summary[:by_supplier], summary[:total]))
    lines << ''

    if summary[:resolution_samples].zero?
      lines << 'Average resolution: n/a (no resolution data)'
    else
      lines << format('Average resolution: %d px (across %d materials)',
                      summary[:avg_resolution].round, summary[:resolution_samples])
    end
    lines << ''

    lines << 'Map-type coverage:'
    total = summary[:total]
    # Show canonical types first (even at 0), then any extras seen in the data.
    seen = summary[:map_coverage].keys
    order = MAP_TYPES + (seen - MAP_TYPES).sort
    order.each do |mt|
      count = summary[:map_coverage][mt] || 0
      pct = total.zero? ? 0 : (count * 100.0 / total)
      lines << format('  %-10s %4d  (%5.1f%%)', mt, count, pct)
    end

    lines.join("\n")
  end

  # Format a count hash (label -> n) sorted by descending count, with percent.
  def format_counts(counts, total)
    counts.sort_by { |label, n| [-n, label.to_s] }.map do |label, n|
      pct = total.zero? ? 0 : (n * 100.0 / total)
      format('  %-20s %4d  (%5.1f%%)', label, n, pct)
    end
  end

  # CLI entry point.
  def run(argv, input: $stdin, output: $stdout)
    raw =
      if argv.empty?
        input.read
      else
        path = argv[0]
        unless File.file?(path)
          warn "catalog_report: no such file: #{path}"
          return 1
        end
        File.read(path)
      end

    records = parse(raw)
    output.puts render(summarize(records))
    0
  rescue JSON::ParserError => e
    warn "catalog_report: invalid JSON: #{e.message}"
    1
  rescue ArgumentError => e
    warn "catalog_report: #{e.message}"
    1
  end
end

exit(CatalogReport.run(ARGV)) if $PROGRAM_NAME == __FILE__
