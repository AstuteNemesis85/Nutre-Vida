import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react';
import renderSafe from '../../utils/renderSafe';

const ToastContainer = styled(motion.div)`
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 1001;
  max-width: 400px;
  min-width: 300px;
  padding: 16px 20px;
  border-radius: 12px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 500;
  
  ${props => {
    switch (props.type) {
      case 'success':
        return `
          background: rgba(72, 187, 120, 0.15);
          border-color: rgba(72, 187, 120, 0.3);
          color: #68d391;
        `;
      case 'error':
        return `
          background: rgba(245, 101, 101, 0.15);
          border-color: rgba(245, 101, 101, 0.3);
          color: #fc8181;
        `;
      case 'warning':
        return `
          background: rgba(237, 137, 54, 0.15);
          border-color: rgba(237, 137, 54, 0.3);
          color: #f6ad55;
        `;
      default:
        return `
          background: rgba(102, 126, 234, 0.15);
          border-color: rgba(102, 126, 234, 0.3);
          color: #90cdf4;
        `;
    }
  }}
`;

const IconWrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
`;

const Message = styled.div`
  flex: 1;
  font-size: 14px;
  line-height: 1.4;
`;

const CloseButton = styled.button`
  background: none;
  border: none;
  color: currentColor;
  cursor: pointer;
  padding: 4px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0.7;
  transition: all 0.2s ease;
  
  &:hover {
    opacity: 1;
    background: rgba(255, 255, 255, 0.1);
  }
`;

const getIcon = (type) => {
  switch (type) {
    case 'success':
      return <CheckCircle size={20} />;
    case 'error':
      return <AlertCircle size={20} />;
    case 'warning':
      return <AlertTriangle size={20} />;
    default:
      return <Info size={20} />;
  }
};

const Toast = ({ message, type = 'info', onClose }) => {
  return (
    <ToastContainer
      type={type}
      initial={{ opacity: 0, x: 100, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 100, scale: 0.9 }}
      transition={{ duration: 0.3, ease: 'easeOut' }}
    >
      <IconWrapper>
        {getIcon(type)}
      </IconWrapper>
      <Message>{renderSafe(message)}</Message>
      <CloseButton onClick={onClose}>
        <X size={16} />
      </CloseButton>
    </ToastContainer>
  );
};

export default Toast;
