export default function FormField({
  label,
  name,
  value,
  onChange,
  type = "text",
  error,
  required = false,
  children,
  ...props
}) {
  return (
    <label className="form-field">
      <span>{label}</span>
      {children || (
        <input
          name={name}
          type={type}
          value={value}
          onChange={onChange}
          required={required}
          {...props}
        />
      )}
      {error ? <small className="field-error">{error}</small> : null}
    </label>
  );
}
