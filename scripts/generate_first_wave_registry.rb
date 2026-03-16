#!/usr/bin/env ruby
# frozen_string_literal: true

require "fileutils"
require "json"
require "pathname"
require "psych"

ROOT = Pathname(__dir__).parent
SUBSETS_DIR = ROOT.join("configs/subsets")
INDICATIONS_DIR = ROOT.join("configs/indications")
REGISTRIES_DIR = ROOT.join("data_contracts/registries")
DATASET_OUT_DIR = REGISTRIES_DIR.join("dataset_manifests")
CONTRAST_OUT_DIR = REGISTRIES_DIR.join("study_contrasts")

URL_BY_SOURCE = {
  "GEO" => ->(id) { "https://www.ncbi.nlm.nih.gov/geo/query/acc.cgi?acc=#{id}" },
  "GDC" => ->(id) { "https://portal.gdc.cancer.gov/projects/#{id}" },
  "ArrayExpress" => ->(id) { "https://www.ebi.ac.uk/biostudies/arrayexpress/studies/#{id}" }
}.freeze

def slug(value)
  value.downcase.gsub(/[^a-z0-9]+/, "_").gsub(/\A_+|_+\z/, "")
end

def source_url(source, id)
  builder = URL_BY_SOURCE[source]
  builder ? builder.call(id) : nil
end

def analysis_unit(modality)
  case modality
  when /single_cell/i
    "single_cell_pseudobulk"
  when /proteom/i
    "proteomics"
  else
    "bulk_rna"
  end
end

def control_caveat(dataset)
  control = dataset["control_definition"].to_s.downcase
  return "Adjacent or paired non-tumorous tissue is not identical to healthy tissue." if control.include?("adjacent")
  return "The comparator arm comes from pneumothorax tissue rather than healthy donor lung." if control.include?("pneumothorax")
  return "The comparator arm is derived from a curated public project arm rather than the exact paper-level aggregate." if dataset["selection_mode"] == "curated_public_arm"

  nil
end

FileUtils.mkdir_p(DATASET_OUT_DIR)
FileUtils.mkdir_p(CONTRAST_OUT_DIR)

indication_by_benchmark_id = Dir[INDICATIONS_DIR.join("*.yaml").to_s].each_with_object({}) do |path, memo|
  indication = Psych.safe_load(File.read(path), aliases: false)
  benchmark_id = indication["benchmark_id"]
  memo[benchmark_id] = indication if benchmark_id
end

subset_paths = Dir[SUBSETS_DIR.join("*.yaml").to_s].sort
generated = []

subset_paths.each do |subset_path|
  subset = Psych.safe_load(File.read(subset_path), aliases: false)
  indication = indication_by_benchmark_id.fetch(subset["benchmark_id"]) do
    raise KeyError, "No indication config found for benchmark #{subset['benchmark_id']}"
  end

  dataset_index = indication.fetch("datasets", []).each_with_object({}) do |dataset, memo|
    memo[dataset["id"]] = dataset
  end
  primary_source_url = indication.fetch("primary_sources").first.fetch("url")
  ontology_ids = indication.fetch("indication").fetch("ontology_ids")
  indication_name = indication.fetch("indication").fetch("name")

  subset.fetch("included_datasets").each do |included|
    dataset_id = included.fetch("id")
    dataset = dataset_index.fetch(dataset_id, {})
    source = included.fetch("source")
    accession_url = source_url(source, dataset_id)
    registry_id = "#{subset['subset_id']}_#{slug(dataset_id)}"
    modality = dataset["modality"] || "transcriptomics"
    tissue = dataset["tissue"]
    role = dataset["role"] || "discovery"
    case_count = included.dig("sample_counts", "case")
    control_count = included.dig("sample_counts", "control")
    manifest_status = included["selection_mode"] == "requires_subsetting" ? "partial" : "verified"

    manifest = {
      "schema_version" => "0.1.0",
      "dataset_id" => registry_id,
      "benchmark_id" => subset.fetch("benchmark_id"),
      "accession" => {
        "database" => source,
        "id" => dataset_id,
        "url" => accession_url
      },
      "source_publication_url" => primary_source_url,
      "disease_context" => {
        "name" => indication_name,
        "ontology_ids" => ontology_ids
      },
      "modality" => modality,
      "tissue" => tissue,
      "platform" => nil,
      "species" => "Homo sapiens",
      "role" => role,
      "sample_units" => "bulk_sample",
      "cohorts" => [
        {
          "cohort_id" => "case",
          "label" => included.fetch("case_definition"),
          "case_control_status" => "case",
          "disease_subtype" => nil,
          "sample_count" => case_count,
          "status" => manifest_status,
          "notes" => included.fetch("reason")
        },
        {
          "cohort_id" => "control",
          "label" => included["control_definition"] || "control",
          "case_control_status" => "control",
          "disease_subtype" => nil,
          "sample_count" => control_count,
          "status" => manifest_status,
          "notes" => control_caveat(included)
        }
      ],
      "manifest_status" => manifest_status,
      "provenance" => {
        "primary_source_url" => accession_url || primary_source_url,
        "extraction_method" => "generated_from_curated_subset_config",
        "extracted_from_section" => "configs/subsets/#{File.basename(subset_path)}"
      },
      "open_questions" => []
    }

    if dataset["notes"]
      manifest["open_questions"] << "Cross-check the generated registry record against the benchmark-pack note: #{dataset['notes']}"
    end

    contrast = {
      "schema_version" => "0.1.0",
      "contrast_id" => registry_id,
      "benchmark_id" => subset.fetch("benchmark_id"),
      "dataset_ids" => [dataset_id],
      "modality" => modality,
      "tissue" => tissue,
      "case_definition" => included.fetch("case_definition"),
      "control_definition" => included["control_definition"],
      "analysis_unit" => analysis_unit(modality),
      "comparison_label" => "#{dataset_id} curated first-wave contrast",
      "sample_counts" => included["sample_counts"],
      "inclusion_rule_summary" => "Included in curated subset #{subset['subset_id']} because #{included.fetch('reason').downcase}",
      "exclusion_rule_summary" => "Restrict the contrast to the curated case and control arms defined in configs/subsets/#{File.basename(subset_path)}.",
      "leakage_risks" => ["Do not use downstream validation outcomes as discovery-time features."],
      "status" => manifest_status,
      "provenance" => {
        "primary_source_url" => accession_url || primary_source_url,
        "notes" => "Generated from curated subset #{subset['subset_id']}."
      }
    }
    caveat = control_caveat(included)
    contrast["leakage_risks"] << caveat if caveat

    dataset_file = DATASET_OUT_DIR.join("dataset_manifest.#{registry_id}.json")
    contrast_file = CONTRAST_OUT_DIR.join("study_contrast.#{registry_id}.json")
    dataset_file.write(JSON.pretty_generate(manifest) + "\n")
    contrast_file.write(JSON.pretty_generate(contrast) + "\n")
    generated << dataset_file.relative_path_from(ROOT).to_s
    generated << contrast_file.relative_path_from(ROOT).to_s
  end
end

puts "Generated #{generated.length} registry artifact(s):"
generated.each { |path| puts "- #{path}" }
