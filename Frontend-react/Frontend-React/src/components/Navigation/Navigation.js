import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, 
  Camera, 
  History, 
  Calendar, 
  User, 
  LogOut, 
  Menu, 
  X,
  Zap
} from 'lucide-react';
import { useApp } from '../../App';

const NavContainer = styled(motion.nav)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  background: rgba(15, 15, 35, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0 20px;
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

const Logo = styled(motion.div)`
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
`;

const LogoIcon = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  box-shadow: 0 0 20px rgba(102, 126, 234, 0.3);
`;

const LogoText = styled.h1`
  font-family: 'Orbitron', monospace;
  font-size: 1.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
`;

const NavLinks = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  
  @media (max-width: 768px) {
    display: none;
  }
`;

const NavLink = styled(motion.button)`
  background: ${props => props.active ? 'rgba(102, 126, 234, 0.2)' : 'transparent'};
  border: 1px solid ${props => props.active ? 'rgba(102, 126, 234, 0.3)' : 'transparent'};
  color: ${props => props.active ? '#90cdf4' : 'rgba(255, 255, 255, 0.7)'};
  padding: 10px 16px;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.3s ease;
  font-family: 'Inter', sans-serif;
  
  &:hover {
    background: rgba(102, 126, 234, 0.15);
    border-color: rgba(102, 126, 234, 0.3);
    color: #90cdf4;
    transform: translateY(-1px);
  }
  
  svg {
    width: 18px;
    height: 18px;
  }
`;

const UserSection = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
  
  @media (max-width: 768px) {
    display: none;
  }
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
`;

const UserAvatar = styled.img`
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: 2px solid rgba(102, 126, 234, 0.3);
`;

const UserName = styled.span`
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
  font-weight: 500;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;

const LogoutButton = styled(motion.button)`
  background: rgba(245, 101, 101, 0.15);
  border: 1px solid rgba(245, 101, 101, 0.3);
  color: #fc8181;
  padding: 10px 16px;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(245, 101, 101, 0.25);
    transform: translateY(-1px);
  }
`;

const MobileMenuButton = styled(motion.button)`
  display: none;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  
  @media (max-width: 768px) {
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  &:hover {
    background: rgba(255, 255, 255, 0.1);
  }
`;

const MobileMenu = styled(motion.div)`
  position: fixed;
  top: 70px;
  left: 0;
  right: 0;
  background: rgba(15, 15, 35, 0.98);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 20px;
  z-index: 99;
  
  @media (min-width: 769px) {
    display: none;
  }
`;

const MobileNavLinks = styled.div`
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
`;

const MobileNavLink = styled(motion.button)`
  background: ${props => props.active ? 'rgba(102, 126, 234, 0.2)' : 'transparent'};
  border: 1px solid ${props => props.active ? 'rgba(102, 126, 234, 0.3)' : 'rgba(255, 255, 255, 0.1)'};
  color: ${props => props.active ? '#90cdf4' : 'rgba(255, 255, 255, 0.8)'};
  padding: 16px 20px;
  border-radius: 12px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 1rem;
  font-weight: 500;
  transition: all 0.3s ease;
  width: 100%;
  text-align: left;
  
  &:hover {
    background: rgba(102, 126, 234, 0.15);
    border-color: rgba(102, 126, 234, 0.3);
  }
`;

const MobileUserSection = styled.div`
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 12px;
`;

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: Home },
  { path: '/analyze', label: 'Analyze Food', icon: Camera },
  { path: '/history', label: 'History', icon: History },
  { path: '/meal-plan', label: 'Meal Plan', icon: Calendar }
];

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useApp();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleNavigation = (path) => {
    navigate(path);
    setMobileMenuOpen(false);
  };

  const handleLogout = () => {
    logout();
    setMobileMenuOpen(false);
  };

  return (
    <>
      <NavContainer
        initial={{ y: -70 }}
        animate={{ y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <Logo
          onClick={() => handleNavigation('/dashboard')}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          <LogoIcon>
            <Zap size={20} />
          </LogoIcon>
          <LogoText>Nutre-Vida</LogoText>
        </Logo>

        <NavLinks>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            
            return (
              <NavLink
                key={item.path}
                active={isActive}
                onClick={() => handleNavigation(item.path)}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Icon />
                {item.label}
              </NavLink>
            );
          })}
        </NavLinks>

        <UserSection>
          {user && (
            <UserInfo>
              {user.picture && (
                <UserAvatar src={user.picture} alt={user.name} />
              )}
              <UserName>{user.name || user.email}</UserName>
            </UserInfo>
          )}
          <LogoutButton
            onClick={handleLogout}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <LogOut size={16} />
            Logout
          </LogoutButton>
        </UserSection>

        <MobileMenuButton
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          whileTap={{ scale: 0.95 }}
        >
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </MobileMenuButton>
      </NavContainer>

      <AnimatePresence>
        {mobileMenuOpen && (
          <MobileMenu
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3 }}
          >
            <MobileNavLinks>
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive = location.pathname === item.path;
                
                return (
                  <MobileNavLink
                    key={item.path}
                    active={isActive}
                    onClick={() => handleNavigation(item.path)}
                    whileTap={{ scale: 0.98 }}
                  >
                    <Icon />
                    {item.label}
                  </MobileNavLink>
                );
              })}
            </MobileNavLinks>

            <MobileUserSection>
              {user && (
                <UserInfo>
                  {user.picture && (
                    <UserAvatar src={user.picture} alt={user.name} />
                  )}
                  <UserName>{user.name || user.email}</UserName>
                </UserInfo>
              )}
              <LogoutButton
                onClick={handleLogout}
                whileTap={{ scale: 0.98 }}
              >
                <LogOut size={16} />
                Logout
              </LogoutButton>
            </MobileUserSection>
          </MobileMenu>
        )}
      </AnimatePresence>
    </>
  );
};

export default Navigation;
