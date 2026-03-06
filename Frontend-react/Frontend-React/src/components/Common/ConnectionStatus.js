import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { Wifi, WifiOff } from 'lucide-react';

const StatusContainer = styled(motion.div)`
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  padding: 8px 16px;
  border-radius: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-family: 'Orbitron', monospace;
  
  ${props => props.status === 'online' ? `
    background: rgba(72, 187, 120, 0.15);
    border-color: rgba(72, 187, 120, 0.3);
    color: #68d391;
    box-shadow: 0 0 20px rgba(72, 187, 120, 0.2);
  ` : `
    background: rgba(245, 101, 101, 0.15);
    border-color: rgba(245, 101, 101, 0.3);
    color: #fc8181;
    box-shadow: 0 0 20px rgba(245, 101, 101, 0.2);
  `}
`;

const IconWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
`;

const StatusText = styled.span`
  font-size: 11px;
`;

const ConnectionStatus = ({ status }) => {
  return (
    <StatusContainer
      status={status}
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      <IconWrapper>
        {status === 'online' ? (
          <Wifi size={14} />
        ) : (
          <WifiOff size={14} />
        )}
      </IconWrapper>
      <StatusText>
        {status === 'online' ? 'Connected' : 'Offline'}
      </StatusText>
    </StatusContainer>
  );
};

export default ConnectionStatus;
