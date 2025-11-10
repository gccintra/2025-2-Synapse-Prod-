import React, { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "react-toastify";
import DynamicHeader from "../components/DynamicHeader"; // Import the new DynamicHeader
import AnimatedPage from "../components/AnimatedPage";
import { usersAPI } from "../services/api";

// Importe os ícones que você está usando no formulário
import UserIcon from "../icons/user-regular-full.svg";
import EnvelopeIcon from "../icons/envelope-regular-full.svg";
import CalendarIcon from "../icons/calendar-regular-full.svg";

// Função auxiliar para ler um cookie pelo nome
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}

function EditAccount() {
  // Hook para navegação programática
  const navigate = useNavigate();

  // Estado para os dados do formulário
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    birthdate: "",
  });

  // erros de validação
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(true);

  // useEffect para buscar os dados do usuário ao carregar o componente
  useEffect(() => {
    const fetchUserData = async () => {
      setLoading(true);

      try {
        const response = await usersAPI.getUserProfile();
        if (response.success) {
          const birthdateFromAPI = response.data.birthdate;
          const date = new Date(birthdateFromAPI);
          const userTimezoneOffset = date.getTimezoneOffset() * 60000;
          const adjustedDate = new Date(date.getTime() + userTimezoneOffset);
          const formattedDate = adjustedDate.toISOString().split("T")[0];

          setFormData({
            fullName: response.data.full_name,
            email: response.data.email,
            birthdate: formattedDate,
          });
        } else {
          toast.error(response.error || "Could not load data.");
        }
      } catch (err) {
        toast.error(err.message || "Connection error. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchUserData();
  }, []);
  const validateForm = () => {
    const newErrors = {};

    if (!formData.fullName.trim()) {
      newErrors.fullName = "Full name is required.";
    }

    if (!formData.email.trim() || !/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "The email is invalid.";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({ ...prevData, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setLoading(true);

    if (!validateForm()) {
      toast.error("Please correct the errors in the form.");
      setLoading(false);
      return;
    }

    const userData = {
      full_name: formData.fullName,
      email: formData.email,
      birthdate: formData.birthdate,
    };

    try {
      const response = await usersAPI.updateUserProfile(userData);

      if (response.success) {
        toast.success(`Data updated successfully!`);
        // delay para o usuário ver a mensagem e depois redireciona
        setTimeout(() => {
          navigate("/account");
        }, 2000);
      } else {
        toast.error(response.error || "An unknown error occurred.");
      }
    } catch (err) {
      toast.error(err.message || "Could not connect to the server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatedPage>
      <DynamicHeader
        userEmail={formData.email}
        isAuthenticated={true}
        onBackClick={() => navigate(-1)}
        backText="Back"
      />
      {/* Container principal da página de edição */}
      <div className="h-[calc(100vh-10rem)] flex flex-col justify-start items-center bg-[#f5f5f5] pt-16">
        <div className="w-full max-w-lg px-4">
          <div className="w-full text-center">
            <h2 className=" mb-2 text-xl md:text-2xl font-bold text-black font-montserrat">
              Edit Your Account Information
            </h2>
            <p className="mt-4 mb-8 text-xs md:text-sm text-gray-600 font-montserrat">
              Edit your account information and confirm.
            </p>
          </div>

          {/* Formulário com os campos */}
          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            {/* Campo Nome Completo */}
            <div className="relative">
              <label
                className="mt-6 block text-xs md:text-sm font-medium text-gray-900 font-montserrat"
                htmlFor="fullName"
              >
                Full Name
                <div className="relative mt-1">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                    {/* Usa o ícone do padrão de cadastro */}
                    <img src={UserIcon} alt="user icon" className="h-5 w-5" />
                  </div>
                  <input
                    id="fullName"
                    name="fullName"
                    type="text"
                    value={formData.fullName}
                    onChange={handleChange}
                    placeholder="Enter your name..."
                    className={`w-full border rounded py-4 px-9 md:py-2 md:px-9 focus:outline-none focus:ring-1 font-montserrat ${
                      errors.fullName
                        ? "border-red-500 focus:ring-red-500"
                        : "border-gray-800 focus:ring-black"
                    }`}
                  />
                </div>
                {errors.fullName && (
                  <p className="mt-1 text-sm text-red-600 font-montserrat">
                    {errors.fullName}
                  </p>
                )}
              </label>
            </div>

            {/* Campo Email */}
            <div className="relative">
              <label
                className="mt-6 block text-xs md:text-sm font-medium text-gray-900 font-montserrat"
                htmlFor="email"
              >
                Email Address
                <div className="relative mt-1">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                    {/* Usa o ícone do padrão de cadastro */}
                    <img
                      src={EnvelopeIcon}
                      alt="email icon"
                      className="h-5 w-5"
                    />
                  </div>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    value={formData.email}
                    onChange={handleChange}
                    placeholder="Enter your e-mail..."
                    className={`w-full border rounded py-4 px-9 md:py-2 md:px-9 focus:outline-none focus:ring-1 font-montserrat ${
                      errors.email
                        ? "border-red-500 focus:ring-red-500"
                        : "border-gray-800 focus:ring-black"
                    }`}
                  />
                </div>
                {errors.email && (
                  <p className="mt-1 text-sm text-red-600 font-montserrat">
                    {errors.email}
                  </p>
                )}
              </label>
            </div>

            {/* Campo Data de Nascimento */}
            <div className="relative">
              <label
                className="mt-6 block text-xs md:text-sm font-medium text-gray-900 font-montserrat"
                htmlFor="birthdate"
              >
                Birthdate
                <div className="relative mt-1">
                  <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                    <img
                      src={CalendarIcon}
                      alt="calendar icon"
                      className="h-5 w-5"
                    />
                  </div>
                  <input
                    id="birthdate"
                    name="birthdate"
                    type="date"
                    value={formData.birthdate}
                    onChange={handleChange}
                    className="w-full border rounded py-4 px-9 md:py-2 md:px-9 focus:outline-none focus:ring-1 font-montserrat border-gray-800 focus:ring-black [&::-webkit-calendar-picker-indicator]:hidden"
                  />
                </div>
              </label>
            </div>

            {/* Botão de Confirmação com o mesmo estilo de 'Cadastrar' */}
            <button
              type="submit"
              className="mt-6 w-full rounded-md bg-black py-3 px-3 md:py-3 md:px-5 text-white font-medium md:font-bold hover:bg-gray-900"
              disabled={loading}
            >
              {loading ? "Confirming..." : "Confirm"}
            </button>
          </form>
        </div>
      </div>
    </AnimatedPage>
  );
}

export default EditAccount;
