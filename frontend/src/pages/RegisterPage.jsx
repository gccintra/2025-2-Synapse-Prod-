import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";

import FormField from "../components/FormField";
import emailIcon from "../icons/envelope-regular-full.svg";
import userIcon from "../icons/user-regular-full.svg";
import calendarIcon from "../icons/calendar-regular-full.svg";
import lockIcon from "../icons/lock-regular-full.svg";
import H2Login from "../components/H2Login";

function RegisterPage() {
  // 1. Estados para armazenar os dados do formulário
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [birthdate, setBirthdate] = useState("");
  const navigate = useNavigate();

  // Estados para feedback da API e validação
  const [errors, setErrors] = useState({});

  const uppercaseRegex = /[A-Z]/;
  const lowercaseRegex = /[a-z]/;
  const numberRegex = /[0-9]/;

  const validateForm = () => {
    const newErrors = {};

    if (!fullName.trim()) {
      newErrors.fullName = "Full name is required.";
    }

    if (!email.trim() || !/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = "The email is invalid.";
    }

    if (
      password.length < 8 ||
      !uppercaseRegex.test(password) ||
      !lowercaseRegex.test(password) ||
      !numberRegex.test(password)
    ) {
      newErrors.password =
        "Password must be at least 8 characters long, with one uppercase letter, one lowercase letter, and one number.";
    }

    if (password !== confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // 3. Função que lida com o envio do formulário
  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!validateForm()) {
      toast.error("Please correct the errors in the form.");
      return;
    }

    const userData = {
      full_name: fullName,
      email: email,
      password: password,
      birthdate: birthdate,
    };

    try {
      const apiUrl = import.meta.env.VITE_API_BASE_URL;

      const response = await fetch(`${apiUrl}/users/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(userData),
      });

      const data = await response.json();

      if (response.ok) {
        toast.success(`User registered successfully! Redirecting to login...`);
        setTimeout(() => {
          navigate("/login");
        }, 2000);
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
          <form
            onSubmit={handleSubmit}
            className="-mt-4 space-y-2 md:space-y-4"
          >
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
              id="fullName"
              label="Full Name"
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Enter your name..."
              error={errors.fullName}
              iconSrc={userIcon}
              iconAlt="user icon"
              required
            />
            <FormField
              id="birthdate"
              label="Birthdate"
              type="date"
              value={birthdate}
              onChange={(e) => setBirthdate(e.target.value)}
              error={errors.birthdate}
              iconSrc={calendarIcon}
              iconAlt="calendar icon"
              required
              className="w-full border rounded py-2 px-9 focus:outline-none focus:ring-1 font-montserrat border-gray-800 focus:ring-black [&::-webkit-calendar-picker-indicator]:hidden"
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
            <FormField
              id="confirmPassword"
              label="Confirm Password"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm your password..."
              error={errors.confirmPassword}
              iconSrc={lockIcon}
              iconAlt="lock icon"
              required
            />
            <button
              type="submit"
              className="mt-3 w-full text-sm rounded-md bg-black py-3 px-5 text-white font-bold md:font-medium hover:bg-gray-900 md:mt-6 font-montserrat"
            >
              Sign Up
            </button>
          </form>

          <p className="mt-4 border-t border-[#111] pt-3 text-center text-xs text-black font-montserrat">
            Already have an account?{" "}
            <Link
              to="/login"
              className="rounded px-0.5 pt-0.5 font-medium text-[#111] no-underline hover:bg-[#1c1c1c] hover:text-[#fff] hover:underline"
            >
              Login here
            </Link>
          </p>
        </div>
      </div>

      {/* Lado direito da tela*/}
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

export default RegisterPage;
