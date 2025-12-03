import React from "react";
import { twMerge } from "tailwind-merge";

function H2Login({ children, className }) {
  return (
    // O twMerge vai perceber que você passou 'font-bold' e removerá automaticamente o 'font-light'
    <h2
      className={twMerge(
        "font-rajdhani text-160xl font-light leading-none",
        className
      )}
    >
      {children}
    </h2>
  );
}

export default H2Login;
