#!/usr/bin/env ruby
# frozen_string_literal: true

require "json"
require "pathname"
require_relative "lib/simple_schema_validator"

ROOT = Pathname(__dir__).parent
SCHEMA_PATH = ROOT.join("data_contracts/schemas/transcriptomics_gene_stat.schema.json")
FIXTURES_DIR = ROOT.join("data_contracts/fixtures/transcriptomics")

schema = JSON.parse(SCHEMA_PATH.read)
fixture_paths = Dir[FIXTURES_DIR.join("*.jsonl").to_s].sort

if fixture_paths.empty?
  warn "No transcriptomics fixture files found in #{FIXTURES_DIR}"
  exit 1
end

all_errors = []
validated = 0

fixture_paths.each do |fixture_path|
  File.readlines(fixture_path, chomp: true).each_with_index do |line, index|
    next if line.strip.empty?

    begin
      data = JSON.parse(line)
    rescue JSON::ParserError => e
      all_errors << "#{fixture_path}: line #{index + 1}: JSON parse error: #{e.message}"
      next
    end

    errors = []
    SimpleSchemaValidator.validate_node(data, schema, "#{File.basename(fixture_path)}:line#{index + 1}", errors)
    if errors.empty?
      validated += 1
    else
      all_errors.concat(errors.map { |error| "#{fixture_path}: #{error}" })
    end
  end
end

unless all_errors.empty?
  warn "\nTranscriptomics fixture validation failed:"
  all_errors.each { |error| warn "- #{error}" }
  exit 1
end

puts "Validated #{validated} transcriptomics fixture record(s)."
