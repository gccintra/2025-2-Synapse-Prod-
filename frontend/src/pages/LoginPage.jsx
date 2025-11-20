import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";

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

  const GoogleIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="20px" height="20px" className="mr-2">
      <path
        fill="#FFC107"
        d="M43.611,20.083H42V20H24v8h11.303c-1.649,4.657-6.08,8-11.303,8c-6.627,0-12-5.373-12-12c0-6.627,5.373-12,12-12c3.059,0,5.842,1.158,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C12.955,4,4,12.955,4,24c0,11.045,8.955,20,20,20c11.045,0,19.003-7.97,19.611-18.083z"
      />
      <path
        fill="#FF3D00"
        d="M6.306,14.691l6.571,4.819C14.655,15.108,18.961,12,24,12c3.059,0,5.842,1.158,7.961,3.039l5.657-5.657C34.046,6.053,29.268,4,24,4C16.318,4,9.665,8.324,6.306,14.691z"
      />
      <path
        fill="#4CAF50"
        d="M24,44c5.166,0,9.86-1.977,13.409-5.192l-6.19-5.238C29.211,35.091,26.686,36,24,36c-5.202,0-9.629-3.351-11.248-7.969l-6.571,4.819C9.665,39.676,16.318,44,24,44z"
      />
      <path
        fill="#1976D2"
        d="M43.611,20.083H42V20H24v8h11.303c-0.792,2.237-2.231,4.166-4.087,5.571c0.001-0.001,0.002-0.001,0.003-0.002l6.19,5.238C36.971,39.205,44,34,44,24C44,22.659,43.862,21.35,43.611,20.083z"
      />
    </svg>
  );

  const handleSubmit = async (event) => {
    event.preventDefault();

    setErrors({});

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
      <div
        className="
      flex w-full lg:w-1/2 flex-col
      items-center justify-center lg:justify-start
      bg-[#f5f5f5] p-8"
      >
        {/* Container para o "Synapse" - alinhado à esquerda */}
        <div className="mt-12 w-full max-w-lg text-left">
          <h1 className="mb-10 text-64xl font-bold text-black font-rajdhani">Synapse</h1>
        </div>
        <div className="w-full max-w-lg">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Campo Email */}

            <label className="block text-sm font-medium text-gray-900 font-montserrat" htmlFor="email">
              Email Address
              <div className="relative mt-1">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <img src="./src/icons/envelope-regular-full.svg" alt="email icon" className="h-5 w-5" />
                </div>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Enter your e-mail..."
                  className={`w-full border rounded py-2 px-9 focus:outline-none focus:ring-1 font-montserrat ${
                    errors.email ? "border-red-500 focus:ring-red-500" : "border-gray-800 focus:ring-black"
                  }`}
                  required
                />
              </div>
              {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email}</p>}
            </label>
            {/* Campo de Senha */}
            <label className="mt-6 block text-sm font-medium text-gray-900 font-montserrat" htmlFor="password">
              Password
              <div className="relative mt-1">
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <img src="./src/icons/lock-regular-full.svg" alt="lock icon" className="h-5 w-5" />
                </div>
                <input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Your password..."
                  className={`w-full border rounded py-2 px-9 focus:outline-none focus:ring-1 font-montserrat ${
                    errors.password ? "border-red-500 focus:ring-red-500" : "border-gray-800 focus:ring-black"
                  }`}
                  required
                />
              </div>
              {errors.password && <p className="mt-1 text-sm text-red-600">{errors.password}</p>}
            </label>

            {/* Links Adicionais */}
            <div className="flex justify-between items-center text-sm font-montserrat">
              <div className="flex items-center">
                <input
                  id="remember-me"
                  type="checkbox"
                  className="h-4 w-4 text-black border-gray-300 rounded py-2
                 px-7"
                />
                <label htmlFor="remember-me" className="ml-2 block text-gray-900 pt-0.2">
                  Remember me
                </label>
              </div>
              <a
                href="#"
                className="font-medium text-[#111] no-underline hover:underline hover:bg-[#1c1c1c] hover:text-[#fff] pt-0.2 px-0.5"
              >
                Forgot my password
              </a>
            </div>

            <button type="submit" className="mt-8 w-full rounded-md bg-black py-3 px-5 text-white hover:bg-gray-900">
              Sign In
            </button>

            <button
              type="button"
              onClick={""}
              disabled={""}
              className={`w-full rounded-lg py-3 px-5 mt-4 text-gray-700 font-semibold border border-gray-300 bg-white hover:bg-gray-50 shadow-sm transition duration-200 flex items-center justify-center`}
            >
              <GoogleIcon />
              Login com Google
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-black border-t border-[#111] pt-3">
            Don't have an account?{" "}
            <Link
              to="/registrar"
              className="font-medium text-[#111] no-underline hover:underline hover:bg-[#1c1c1c] hover:text-[#fff] pt-0.2 px-0.5"
            >
              Sign up here
            </Link>
          </p>
        </div>
      </div>

      {/* Lado direito (design system) */}
      <div className="hidden lg:flex w-full lg:w-1/2 flex-col items-left justify-center bg-black p-4 sm:p-8 text-white">
        <h2 className="ml-8 text-160xl font-light leading-none font-rajdhani">Know</h2>
        <h2 className="ml-8 text-160xl font-light leading-none font-rajdhani">Your</h2>
        <h2 className="ml-8 text-160xl font-light leading-none font-rajdhani">World,</h2>
        <h2 className="ml-8 text-160xl font-bold leading-none font-rajdhani">
          <Link to="/feed" className="hover:text-gray-300 transition-colors duration-200">
            <button>Faster.</button>
          </Link>
        </h2>
      </div>
    </div>
  );
}

export default LoginPage;
