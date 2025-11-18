import React from "react";

function FormField({
  id,
  label,
  type,
  value,
  onChange,
  placeholder,
  error,
  iconSrc,
  iconAlt,
  ...props
}) {
  return (
    <label
      className="block text-sm md:text-xs font-medium text-gray-900 font-montserrat"
      htmlFor={id}
    >
      {label}
      <div className="relative mt-3 md:mt-2">
        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
          <img src={iconSrc} alt={iconAlt} className="h-5 w-5" />
        </div>
        <input
          id={id}
          type={type}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          className={`w-full border rounded py-3 px-8 md:py-2 md:px-9 focus:outline-none focus:ring-1 font-montserrat ${
            error
              ? "border-red-500 focus:ring-red-500"
              : "border-gray-800 focus:ring-black"
          }`}
          {...props}
        />
      </div>
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </label>
  );
}

export default FormField;
