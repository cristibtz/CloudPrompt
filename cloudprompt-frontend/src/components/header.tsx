import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
} from "@/components/ui/navigation-menu"
import { useState } from "react"
import { useKeycloak } from "../auth/KeycloakContext"

export function Header() {
    const [isMenuOpen, setIsMenuOpen] = useState(false)
    const { authenticated, logout, keycloak } = useKeycloak()

    return (
        <header className="bg-[#0B1C37] text-white p-4 w-full border-b border-[#B0BEC5]/20">
            {/* Desktop Layout */}
            <div className="container mx-auto hidden lg:grid grid-cols-3 items-center">
                {/* Column 1: Logo and Brand */}
                <div className="flex items-center space-x-4">
                    <img 
                        src="/logo.png"
                        alt="CloudPrompt Logo"
                        className="w-24 h-24 drop-shadow-lg"
                    />
                    <h1 className="text-3xl font-bold text-white drop-shadow-sm">
                        Cloud<span className="text-[#6565fc]">Prompt</span>
                    </h1>
                </div>
                
                {/* Column 2: Navigation Menu (Centered) */}
                <NavigationMenu className="flex justify-center">
                    <NavigationMenuList className="space-x-4">
                        <NavigationMenuItem className="bg-[#6565fc] rounded-md hover:bg-[#512DA8] transition-colors duration-300">
                            <NavigationMenuLink 
                                href="/"
                                className="text-[#000000] text-lg font-semibold px-4 py-2 hover:text-[white] transition-colors duration-300"
                                >
                                Home
                            </NavigationMenuLink>
                        </NavigationMenuItem>

                        <NavigationMenuItem className="bg-[#6565fc] rounded-md hover:bg-[#512DA8] transition-colors duration-300">
                            <NavigationMenuLink 
                                href="#" 
                                className="text-[#000000] text-lg font-semibold px-4 py-2 hover:text-[white] transition-colors duration-300"
                                >
                                User Profile
                            </NavigationMenuLink>
                        </NavigationMenuItem>
                    </NavigationMenuList>
                </NavigationMenu>

                <div className="flex justify-end items-center space-x-4">
                    {authenticated && (
                        <>
                            <span className="text-sm text-gray-300">
                                Welcome, {keycloak?.tokenParsed?.preferred_username || 'User'}
                            </span>
                            <button
                                onClick={logout}
                                className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-md text-white text-sm font-medium transition-colors duration-300"
                            >
                                Logout
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* Mobile Layout */}
            <div className="container mx-auto lg:hidden">
                <div className="flex items-center justify-between">
                    {/* Mobile Logo */}
                    <div className="flex items-center space-x-3">
                        <img 
                            src="/logo.png"
                            alt="CloudPrompt Logo"
                            className="w-12 h-12 drop-shadow-lg"
                        />
                        <h1 className="text-xl font-bold text-white drop-shadow-sm">
                            Cloud<span className="text-[#6565fc]">Prompt</span>
                        </h1>
                    </div>

                    {/* Mobile Menu Button */}
                    <button 
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                        className="p-2 rounded-md hover:bg-[#B0BEC5]/20 transition-colors duration-300"
                        aria-label="Toggle menu"
                    >
                        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            {isMenuOpen ? (
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                            ) : (
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                            )}
                        </svg>
                    </button>
                </div>

                {/* Mobile Menu (Collapsible) */}
                {isMenuOpen && (
                    <div className="mt-4 space-y-2 border-t border-[#B0BEC5]/20 pt-4">
                        <a 
                            href="/"
                            className="block w-full text-left px-4 py-3 bg-[#6565fc] rounded-md hover:bg-[#512DA8] transition-colors duration-300 text-[#000000] text-lg font-semibold hover:text-white"
                        >
                            Home
                        </a>
                        <a 
                            href="#"
                            className="block w-full text-left px-4 py-3 bg-[#6565fc] rounded-md hover:bg-[#512DA8] transition-colors duration-300 text-[#000000] text-lg font-semibold hover:text-white"
                        >
                            User Profile
                        </a>
                        {authenticated && (
                            <button
                                onClick={logout}
                                className="block w-full text-left px-4 py-3 bg-red-600 rounded-md hover:bg-red-700 transition-colors duration-300 text-white text-lg font-semibold"
                            >
                                Logout
                            </button>
                        )}
                    </div>
                )}
            </div>
        </header>
    )
}