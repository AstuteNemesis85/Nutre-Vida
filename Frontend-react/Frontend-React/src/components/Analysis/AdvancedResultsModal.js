import React from 'react';
import styled from 'styled-components';
import { motion } from 'framer-motion';
import { X, ChefHat, RefreshCw, Lightbulb } from 'lucide-react';

const ModalOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  justify  return (
    <ModalOverlay
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <ModalContent
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={e => e.stopPropagation()}
      >
        <CloseButton onClick={onClose}>
          <X size={24} />
        </CloseButton>
        {renderContent()}
      </ModalContent>
    </ModalOverlay>
  );align-items: center;
  z-index: 1000;
  backdrop-filter: blur(8px);
`;

const ModalContent = styled(motion.div)`
  background: rgba(23, 25, 35, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 24px;
  padding: 40px;
  width: 90%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
`;

const CloseButton = styled.button`
  position: absolute;
  top: 20px;
  right: 20px;
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  padding: 8px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;

  &:hover {
    color: white;
    background: rgba(255, 255, 255, 0.1);
  }
`;

const Title = styled.h2`
  font-family: 'Orbitron', monospace;
  font-size: 1.8rem;
  color: white;
  margin-bottom: 30px;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const ContentSection = styled.div`
  margin-bottom: 30px;
`;

const RecipeSection = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
`;

const RecipeTitle = styled.h3`
  color: white;
  font-size: 1.4rem;
  margin-bottom: 20px;
  font-family: 'Orbitron', monospace;
`;

const RecipeInfo = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
`;

const InfoItem = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 16px;
`;

const InfoLabel = styled.div`
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
  margin-bottom: 8px;
`;

const InfoValue = styled.div`
  color: white;
  font-weight: 600;
`;

const RecipeSection2 = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const SubSection = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 20px;
`;

const SubTitle = styled.h4`
  color: white;
  font-size: 1.1rem;
  margin-bottom: 15px;
  font-family: 'Orbitron', monospace;
`;

const List = styled.ul`
  list-style: none;
  padding: 0;
  margin: 0;
`;

const ListItem = styled.li`
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 12px;
  padding-left: 24px;
  position: relative;

  &:before {
    content: '•';
    position: absolute;
    left: 8px;
    color: #667eea;
  }
`;

const SwapItem = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  display: grid;
  grid-template-columns: 1fr auto;
  gap: 20px;
  align-items: center;
`;

const SwapInfo = styled.div``;

const SwapOriginal = styled.div`
  color: rgba(255, 255, 255, 0.7);
  text-decoration: line-through;
  margin-bottom: 8px;
`;

const SwapNew = styled.div`
  color: #48bb78;
  font-weight: 600;
`;

const SwapBenefits = styled.div`
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
  margin-top: 8px;
`;

const InsightCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 24px;
  margin-bottom: 20px;
`;

const InsightTitle = styled.h4`
  color: white;
  font-size: 1.2rem;
  margin-bottom: 12px;
  font-family: 'Orbitron', monospace;
`;

const InsightDescription = styled.p`
  color: rgba(255, 255, 255, 0.8);
  line-height: 1.6;
`;

const TipsList = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-top: 20px;
`;

const Tip = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 16px;
`;

const TipTitle = styled.h5`
  color: white;
  font-size: 1rem;
  margin-bottom: 8px;
`;

const TipText = styled.p`
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  line-height: 1.5;
`;

const AdvancedResultsModal = ({ isOpen, onClose, type, data }) => {
  if (!isOpen) return null;

  const renderContent = () => {
    switch (type) {
      case 'recipe':
        return (
          <>
            <Title>
              <ChefHat size={24} />
              Generated Recipe
            </Title>
            {data && (
              <ContentSection>
                <RecipeSection>
                  <RecipeTitle>{data.title}</RecipeTitle>
                  <RecipeInfo>
                    <InfoItem>
                      <InfoLabel>Preparation Time</InfoLabel>
                      <InfoValue>{data.prepTime}</InfoValue>
                    </InfoItem>
                    <InfoItem>
                      <InfoLabel>Cooking Time</InfoLabel>
                      <InfoValue>{data.cookTime}</InfoValue>
                    </InfoItem>
                    <InfoItem>
                      <InfoLabel>Difficulty</InfoLabel>
                      <InfoValue>{data.difficulty}</InfoValue>
                    </InfoItem>
                    <InfoItem>
                      <InfoLabel>Servings</InfoLabel>
                      <InfoValue>{data.servings}</InfoValue>
                    </InfoItem>
                  </RecipeInfo>
                  <RecipeSection2>
                    <SubSection>
                      <SubTitle>Ingredients</SubTitle>
                      <List>
                        {data.ingredients?.map((ingredient, index) => (
                          <ListItem key={index}>{ingredient}</ListItem>
                        ))}
                      </List>
                    </SubSection>
                    <SubSection>
                      <SubTitle>Instructions</SubTitle>
                      <List>
                        {data.instructions?.map((step, index) => (
                          <ListItem key={index}>{step}</ListItem>
                        ))}
                      </List>
                    </SubSection>
                  </RecipeSection2>
                </RecipeSection>
              </ContentSection>
            )}
          </>
        );

      case 'swaps':
        return (
          <>
            <Title>
              <RefreshCw size={24} />
              Healthy Alternatives
            </Title>
            {data && data.map((swap, index) => (
              <SwapItem key={index}>
                <SwapInfo>
                  <SwapOriginal>{swap.original}</SwapOriginal>
                  <SwapNew>{swap.alternative}</SwapNew>
                  <SwapBenefits>{swap.benefits}</SwapBenefits>
                </SwapInfo>
              </SwapItem>
            ))}
          </>
        );

      case 'insights':
        return (
          <>
            <Title>
              <Lightbulb size={24} />
              Nutrition Insights
            </Title>
            {data && (
              <>
                <InsightCard>
                  <InsightTitle>Overall Analysis</InsightTitle>
                  <InsightDescription>{data.overview}</InsightDescription>
                </InsightCard>

                <TipsList>
                  {data.recommendations?.map((tip, index) => (
                    <Tip key={index}>
                      <TipTitle>{tip.title}</TipTitle>
                      <TipText>{tip.description}</TipText>
                    </Tip>
                  ))}
                </TipsList>

                {data.macroBreakdown && (
                  <InsightCard>
                    <InsightTitle>Macro Nutrient Balance</InsightTitle>
                    <InsightDescription>{data.macroBreakdown}</InsightDescription>
                  </InsightCard>
                )}
              </>
            )}
          </>
        );

      default:
        return null;
    }
  };

  return (
    <ModalOverlay
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      onClick={onClose}
    >
      <ModalContent
        initial={{ scale: 0.9, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        exit={{ scale: 0.9, opacity: 0 }}
        onClick={e => e.stopPropagation()}
      >
        <CloseButton onClick={onClose}>
          <X size={24} />
        </CloseButton>
        {renderContent()}
      </ModalContent>
    </ModalOverlay>
    </ModalOverlay>
  );
};

export default AdvancedResultsModal;