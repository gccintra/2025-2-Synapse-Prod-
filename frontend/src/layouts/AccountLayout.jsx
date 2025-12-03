import React from "react";
import { Outlet, useLocation, useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import DynamicHeader from "../components/DynamicHeader";
import { useAuthContext } from "../contexts/AuthContext";

const AccountLayout = () => {
  const { user, isAuthenticated } = useAuthContext();
  const location = useLocation();
  const navigate = useNavigate();

  const sectionVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 },
  };

  const isAccountActive = location.pathname === "/account";
  const isNewsletterActive = location.pathname === "/newsletter";

  return (
    <div className="bg-gray-50 min-h-screen">
      <DynamicHeader
        userEmail={user?.email || ""}
        isAuthenticated={isAuthenticated}
        onBackClick={() => navigate("/feed")}
        backText="Back to feed"
      />
      <main className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col items-center min-[670px]:flex-row min-[670px]:items-start">
          <motion.aside
            className="mt-16 w-11/12 min-[670px]:w-1/3 min-[670px]:sticky min-[670px]:top-24 min-[670px]:self-start min-[670px]:ml-12"
            variants={sectionVariants}
            initial="hidden"
            animate="visible"
          >
            <div className="h-full">
              <nav>
                <ul className="space-y-1">
                  <motion.li layout className="relative">
                    <Link
                      to="/account"
                      className={`block w-full py-2 pl-4 text-base font-montserrat transition-colors duration-200 ${
                        isAccountActive
                          ? "font-semibold text-black"
                          : "font-medium text-gray-500 hover:text-black"
                      }`}
                    >
                      Account
                    </Link>
                    {isAccountActive && (
                      <motion.div
                        className="absolute left-0 top-1/4 h-1/2 w-1.5 -translate-y-1/3 bg-black"
                        layoutId="active-sidebar-indicator"
                        transition={{
                          type: "spring",
                          stiffness: 300,
                          damping: 30,
                        }}
                      />
                    )}
                  </motion.li>
                  <motion.li layout className="relative">
                    <Link
                      to="/newsletter"
                      className={`block w-full py-2 pl-4 text-base font-montserrat transition-colors duration-200 ${
                        isNewsletterActive
                          ? "font-semibold text-black"
                          : "font-medium text-gray-500 hover:text-black"
                      }`}
                    >
                      Newsletter
                    </Link>
                    {isNewsletterActive && (
                      <motion.div
                        className="absolute left-0 top-1/4 h-1/2 w-1.5 -translate-y-1/3 bg-black"
                        layoutId="active-sidebar-indicator"
                        transition={{
                          type: "spring",
                          stiffness: 300,
                          damping: 30,
                        }}
                      />
                    )}
                  </motion.li>
                </ul>
              </nav>
            </div>
          </motion.aside>
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default AccountLayout;
