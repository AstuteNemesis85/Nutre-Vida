import React, { useEffect } from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { Zap, Shield, Brain, TrendingUp } from 'lucide-react';
import { useApp } from '../../App';

const LoginContainer = styled(motion.div)`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
`;

const LoginCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 60px 40px;
  max-width: 500px;
  width: 100%;
  text-align: center;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, #667eea, #764ba2, #48bb78);
    animation: shimmer 3s ease-in-out infinite;
  }
  
  @keyframes shimmer {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
  }
`;

const Logo = styled(motion.div)`
  margin-bottom: 40px;
`;

const LogoText = styled.h1`
  font-family: 'Orbitron', monospace;
  font-size: 3.5rem;
  font-weight: 900;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #48bb78 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 10px;
  text-shadow: 0 0 30px rgba(102, 126, 234, 0.3);
`;

const Tagline = styled.p`
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 50px;
  font-weight: 300;
`;

const FeatureGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 40px;
`;

const FeatureItem = styled(motion.div)`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.05);
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(102, 126, 234, 0.3);
    transform: translateY(-2px);
  }
`;

const FeatureIcon = styled.div`
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
  color: white;
`;

const FeatureTitle = styled.h3`
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 4px;
  font-family: 'Orbitron', monospace;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const FeatureDesc = styled.p`
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
  line-height: 1.4;
`;

const GoogleSignInWrapper = styled.div`
  display: flex;
  justify-content: center;
  margin-bottom: 30px;
  
  .g_id_signin {
    filter: brightness(1.1) contrast(1.1);
    border-radius: 12px !important;
    transition: all 0.3s ease;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
    }
  }
`;

const PoweredBy = styled.p`
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 20px;
  font-family: 'Orbitron', monospace;
  text-transform: uppercase;
  letter-spacing: 1px;
`;

const features = [
  {
    icon: <Brain size={24} />,
    title: 'AI Analysis',
    desc: 'Advanced computer vision for food recognition'
  },
  {
    icon: <TrendingUp size={24} />,
    title: 'Smart Tracking',
    desc: 'Personalized nutrition insights & recommendations'
  },
  {
    icon: <Zap size={24} />,
    title: 'Instant Results',
    desc: 'Get nutrition data in seconds'
  },
  {
    icon: <Shield size={24} />,
    title: 'Secure & Private',
    desc: 'Your data is protected with enterprise security'
  }
];

const Login = () => {
  const { GOOGLE_CLIENT_ID, login } = useApp();

  useEffect(() => {
    // Initialize Google Sign-In
    if (window.google) {
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleCredentialResponse,
        auto_prompt: false
      });

      window.google.accounts.id.renderButton(
        document.getElementById('google-signin-button'),
        {
          type: 'standard',
          shape: 'rectangular',
          theme: 'filled_blue',
          text: 'signin_with',
          size: 'large',
          logo_alignment: 'left'
        }
      );
    }
  }, [GOOGLE_CLIENT_ID]);

  const handleCredentialResponse = (response) => {
    const responsePayload = decodeJwtResponse(response.credential);
    
    login({
      google_id: responsePayload.sub,
      email: responsePayload.email,
      name: responsePayload.name,
      picture: responsePayload.picture
    });
  };

  const decodeJwtResponse = (token) => {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  };

  return (
    <LoginContainer
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.8 }}
    >
      <LoginCard
        initial={{ opacity: 0, y: 50, scale: 0.9 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.8, delay: 0.2 }}
      >
        <Logo
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
        >
          <LogoText>Nutre-Vida</LogoText>
          <Tagline>AI-Powered Nutrition Analysis</Tagline>
        </Logo>

        <FeatureGrid>
          {features.map((feature, index) => (
            <FeatureItem
              key={index}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.6 + index * 0.1 }}
              whileHover={{ scale: 1.05 }}
            >
              <FeatureIcon>{feature.icon}</FeatureIcon>
              <FeatureTitle>{feature.title}</FeatureTitle>
              <FeatureDesc>{feature.desc}</FeatureDesc>
            </FeatureItem>
          ))}
        </FeatureGrid>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 1.0 }}
        >
          <GoogleSignInWrapper>
            <div id="google-signin-button"></div>
          </GoogleSignInWrapper>
          
          <PoweredBy>
            Powered by Advanced AI & Machine Learning
          </PoweredBy>
        </motion.div>
      </LoginCard>
    </LoginContainer>
  );
};

export default Login;
