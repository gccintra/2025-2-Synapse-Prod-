import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";

import FormField from "../components/FormField";
import emailIcon from "../icons/envelope-regular-full.svg";
import lockIcon from "../icons/lock-regular-full.svg";
import H2Login from "../components/H2Login";

function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const navigate = useNavigate();
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const newErrors = {};

    if (!email.trim() || !/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = "The email is invalid.";
    }
    if (!password.trim()) {
      newErrors.password = "Please enter your password.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!validateForm()) {
      toast.error("Please correct the errors in the form.");
      return;
    }

    const userData = {
      email: email,
      password: password,
    };
    try {
      const apiUrl = import.meta.env.VITE_API_BASE_URL;

      const response = await fetch(`${apiUrl}/users/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
        credentials: "include",
      });

      const data = await response.json();

      if (response.ok) {
        toast.success(`Login successful! Welcome, ${data.data.full_name}.`);
        navigate("/");
      } else {
        toast.error(data.error || "An unknown error occurred.");
      }
    } catch (err) {
      toast.error("Could not connect to the server. Please try again later.");
    }
  };

  return (
    <div className="min-h-screen lg:flex bg-[#f5f5f5]">
      {/* Lado esquerdo (formulário) */}
      <div className="flex w-full lg:w-1/2 flex-col items-center justify-center p-6 min-h-screen lg:min-h-0">
        <div className="w-5/6 md:w-full max-w-md">
          <div className="text-left">
            <h1 className="mb-10 text-[56px] md:text-64xl font-bold text-black font-rajdhani">
              Synapse
            </h1>
          </div>
          <form onSubmit={handleSubmit} className="-mt-2 md:-mt-4 space-y-4 ">
            <FormField
              id="email"
              label="Email Address"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your e-mail..."
              error={errors.email}
              iconSrc={emailIcon}
              iconAlt="email icon"
              required
            />

            <FormField
              id="password"
              label="Password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Your password..."
              error={errors.password}
              iconSrc={lockIcon}
              iconAlt="lock icon"
              required
            />

            {/* Links Adicionais */}
            <div className="flex justify-between items-center text-sm font-montserrat">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  type="checkbox"
                  className="mt-3 h-4 w-4 rounded border-gray-300 text-black focus:ring-black"
                />
                <label
                  htmlFor="remember-me"
                  className="mt-3 ml-2 block text-gray-900"
                >
                  Remember me
                </label>
              </div>
              <a
                href="#"
                className="mt-3 rounded px-0.5 pt-0.5 text-sm font-medium text-[#111] no-underline hover:bg-[#1c1c1c] hover:text-[#fff] hover:underline"
              >
                Forgot my password
              </a>
            </div>

            <button
              type="submit"
              className="mt-3 w-full text-sm rounded-md bg-black py-3 px-5 text-white font-bold md:font-medium hover:bg-gray-900 md:mt-6 font-montserrat"
            >
              Sign In
            </button>
          </form>

          <p className="mt-4 border-t border-[#111] pt-3 text-center text-xs text-black font-montserrat">
            Don't have an account?{" "}
            <Link
              to="/registrar"
              className="rounded px-0.5 pt-0.5 font-medium text-[#111] no-underline hover:bg-[#1c1c1c] hover:text-[#fff] hover:underline"
            >
              Sign up here
            </Link>
          </p>
        </div>
      </div>

      {/* Lado direito (design system) */}
      <div className="hidden lg:flex w-full lg:w-1/2 flex-col items-start justify-center bg-black p-8 text-white">
        <div className="ml-12">
          <H2Login>Know</H2Login>
          <H2Login>Your</H2Login>
          <H2Login>World,</H2Login>
          <H2Login className="font-bold">
            <Link
              to="/feed"
              className="transition-colors duration-200 hover:text-gray-300"
            >
              Faster.
            </Link>
          </H2Login>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
