# frozen_string_literal: true

module SimpleSchemaValidator
  module_function

  def matches_type?(value, type_name)
    case type_name
    when "string"
      value.is_a?(String)
    when "object"
      value.is_a?(Hash)
    when "array"
      value.is_a?(Array)
    when "integer"
      value.is_a?(Integer)
    when "number"
      value.is_a?(Numeric)
    when "boolean"
      value == true || value == false
    when "null"
      value.nil?
    else
      false
    end
  end

  def validate_node(value, schema, path, errors)
    if schema.key?("type")
      allowed_types = schema["type"].is_a?(Array) ? schema["type"] : [schema["type"]]
      unless allowed_types.any? { |type_name| matches_type?(value, type_name) }
        errors << "#{path}: expected #{allowed_types.join(' or ')}, got #{value.class}"
        return
      end
    end

    if schema.key?("enum") && !schema["enum"].include?(value)
      errors << "#{path}: expected one of #{schema['enum'].inspect}, got #{value.inspect}"
    end

    return if value.nil?

    case value
    when Hash
      required = schema.fetch("required", [])
      required.each do |key|
        errors << "#{path}: missing required key #{key.inspect}" unless value.key?(key)
      end

      properties = schema.fetch("properties", {})
      if schema["additionalProperties"] == false
        unknown_keys = value.keys - properties.keys
        unknown_keys.each do |key|
          errors << "#{path}: unexpected key #{key.inspect}"
        end
      end

      properties.each do |key, child_schema|
        next unless value.key?(key)

        validate_node(value[key], child_schema, "#{path}.#{key}", errors)
      end
    when Array
      min_items = schema["minItems"]
      if min_items && value.length < min_items
        errors << "#{path}: expected at least #{min_items} items, got #{value.length}"
      end

      item_schema = schema["items"]
      return unless item_schema

      value.each_with_index do |item, index|
        validate_node(item, item_schema, "#{path}[#{index}]", errors)
      end
    end
  end
end
