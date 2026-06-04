// pbr_pack -- group/normalize a list of PBR map filenames into a material
// manifest. Mirrors the Python texture normalizer in the ingestion pipeline:
// it classifies each filename into a canonical PBR map type (albedo, normal,
// roughness, metallic, ao, height, ...) from substrings in the name, then emits
// a small JSON-ish manifest grouping maps under one material slug.
//
// Standard library only (C++17).
//
// Usage:
//   pbr_pack rock_albedo.png rock_normal.png rock_rough.jpg rock_ao.png
//   ls *.png | pbr_pack          # read filenames from stdin (one per line)
//
// Output (example):
//   {
//     "material": "rock",
//     "map_count": 4,
//     "maps": {
//       "albedo":    "rock_albedo.png",
//       "normal":    "rock_normal.png",
//       "roughness": "rock_rough.jpg",
//       "ao":        "rock_ao.png"
//     },
//     "coverage": ["albedo","normal","roughness","ao"],
//     "missing":  ["metallic","height"]
//   }

#include <algorithm>
#include <cctype>
#include <iostream>
#include <map>
#include <string>
#include <utility>
#include <vector>

namespace {

// Lowercase a copy of the string for case-insensitive matching.
std::string to_lower(std::string s) {
    std::transform(s.begin(), s.end(), s.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    return s;
}

// Strip directory components and the file extension, returning the bare stem.
std::string stem(const std::string &path) {
    std::size_t slash = path.find_last_of("/\\");
    std::string base = (slash == std::string::npos) ? path : path.substr(slash + 1);
    std::size_t dot = base.find_last_of('.');
    if (dot != std::string::npos && dot != 0) {
        base = base.substr(0, dot);
    }
    return base;
}

// Canonical map types in a stable, human-meaningful order.
const std::vector<std::string> kCanonical = {
    "albedo", "normal", "roughness", "metallic", "ao", "height"};

// Map each canonical type to the filename substrings that indicate it.
// Order within each list does not matter; classification picks the first
// canonical type whose any-alias matches.
const std::vector<std::pair<std::string, std::vector<std::string>>> kAliases = {
    {"albedo",    {"albedo", "basecolor", "base_color", "diffuse", "diff", "col", "color"}},
    {"normal",    {"normal", "nrm", "norm", "_n_", "_n."}},
    {"roughness", {"roughness", "rough", "_r_", "_r."}},
    {"metallic",  {"metallic", "metalness", "metal", "_m_", "_m."}},
    {"ao",        {"ambientocclusion", "ambient_occlusion", "occlusion", "ao"}},
    {"height",    {"height", "displacement", "disp", "bump"}},
};

// Classify a filename into a canonical map type, or "" if unknown.
std::string classify(const std::string &filename) {
    std::string lo = to_lower(filename);
    for (const auto &entry : kAliases) {
        for (const auto &alias : entry.second) {
            if (lo.find(alias) != std::string::npos) {
                return entry.first;
            }
        }
    }
    return "";
}

// Guess the material slug from a filename: take the stem, then drop a trailing
// token that looks like a map descriptor or a resolution (e.g. "2k", "4096").
std::string material_slug(const std::string &filename) {
    std::string s = to_lower(stem(filename));
    // Split on '_' / '-' / '.' into tokens.
    std::vector<std::string> tokens;
    std::string cur;
    for (char c : s) {
        if (c == '_' || c == '-' || c == '.') {
            if (!cur.empty()) { tokens.push_back(cur); cur.clear(); }
        } else {
            cur.push_back(c);
        }
    }
    if (!cur.empty()) tokens.push_back(cur);

    auto is_resolution = [](const std::string &t) {
        if (t.size() >= 2 && (t.back() == 'k' || t.back() == 'K')) {
            return std::all_of(t.begin(), t.end() - 1, ::isdigit);
        }
        return !t.empty() && std::all_of(t.begin(), t.end(), ::isdigit);
    };

    // Drop trailing map-descriptor and resolution tokens.
    while (!tokens.empty()) {
        const std::string &last = tokens.back();
        if (is_resolution(last) || !classify(last).empty()) {
            tokens.pop_back();
        } else {
            break;
        }
    }
    if (tokens.empty()) return s; // fall back to whole stem
    std::string slug;
    for (std::size_t i = 0; i < tokens.size(); i++) {
        if (i) slug.push_back('_');
        slug += tokens[i];
    }
    return slug;
}

// Minimal JSON string escaping for the values we emit (filenames/slugs).
std::string json_escape(const std::string &s) {
    std::string out;
    for (char c : s) {
        switch (c) {
            case '"':  out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            default:   out += c;       break;
        }
    }
    return out;
}

void print_manifest(const std::string &material,
                    const std::map<std::string, std::string> &maps) {
    std::cout << "{\n";
    std::cout << "  \"material\": \"" << json_escape(material) << "\",\n";
    std::cout << "  \"map_count\": " << maps.size() << ",\n";
    std::cout << "  \"maps\": {";
    bool first = true;
    // Emit in canonical order for stable output.
    for (const auto &type : kCanonical) {
        auto it = maps.find(type);
        if (it == maps.end()) continue;
        std::cout << (first ? "\n" : ",\n");
        std::cout << "    \"" << type << "\": \"" << json_escape(it->second) << "\"";
        first = false;
    }
    std::cout << (first ? "}" : "\n  }") << ",\n";

    // coverage = present canonical types, missing = the rest.
    std::cout << "  \"coverage\": [";
    bool fc = true;
    for (const auto &type : kCanonical) {
        if (maps.count(type)) {
            std::cout << (fc ? "" : ",") << "\"" << type << "\"";
            fc = false;
        }
    }
    std::cout << "],\n";
    std::cout << "  \"missing\": [";
    bool fm = true;
    for (const auto &type : kCanonical) {
        if (!maps.count(type)) {
            std::cout << (fm ? "" : ",") << "\"" << type << "\"";
            fm = false;
        }
    }
    std::cout << "]\n}\n";
}

} // namespace

int main(int argc, char **argv) {
    std::vector<std::string> files;
    if (argc > 1) {
        for (int i = 1; i < argc; i++) files.emplace_back(argv[i]);
    } else {
        std::string line;
        while (std::getline(std::cin, line)) {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            if (!line.empty()) files.push_back(line);
        }
    }

    if (files.empty()) {
        std::cerr << "pbr_pack: no filenames (pass as args or via stdin)\n";
        return 1;
    }

    // Classify into the material slug derived from the first recognizable file.
    std::map<std::string, std::string> maps; // canonical type -> filename
    std::string material;
    for (const auto &f : files) {
        std::string type = classify(f);
        if (material.empty()) material = material_slug(f);
        if (type.empty()) {
            std::cerr << "pbr_pack: warning: could not classify '" << f << "'\n";
            continue;
        }
        // First match for a given type wins; warn on duplicates.
        if (!maps.emplace(type, f).second) {
            std::cerr << "pbr_pack: warning: duplicate " << type
                      << " map ('" << f << "' ignored)\n";
        }
    }

    if (material.empty()) material = "unknown";
    print_manifest(material, maps);
    return 0;
}
