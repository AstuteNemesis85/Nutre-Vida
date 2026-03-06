import { motion } from 'framer-motion';
import { ChefHat, Edit3, Lightbulb, RefreshCw, X } from 'lucide-react';
import styled from 'styled-components';

const ModalOverlay = styled(motion.div)`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  justify-content: center;
  align-items: center;
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
  margin: 0;
  font-size: 0.9rem;
  color: #718096;
`;

const EditForm = styled.div`
  display: grid;
  gap: 20px;
`;

const EditItem = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 20px;
`;

const EditItemTitle = styled.h4`
  color: white;
  font-size: 1.1rem;
  margin-bottom: 15px;
  font-family: 'Orbitron', monospace;
`;

const EditField = styled.div`
  margin-bottom: 15px;
`;

const EditLabel = styled.label`
  display: block;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  margin-bottom: 8px;
`;

const EditInput = styled.input`
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 12px;
  color: white;
  font-size: 1rem;

  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
  }

  &::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }
`;

const EditTextarea = styled.textarea`
  width: 100%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 12px;
  color: white;
  font-size: 1rem;
  min-height: 80px;
  resize: vertical;

  &:focus {
    outline: none;
    border-color: #667eea;
    box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
  }

  &::placeholder {
    color: rgba(255, 255, 255, 0.4);
  }
`;

const EditActions = styled.div`
  display: flex;
  gap: 15px;
  justify-content: flex-end;
  margin-top: 30px;
`;

const EditButton = styled.button`
  background: #667eea;
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;

  &:hover {
    background: #5a67d8;
    transform: translateY(-2px);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;

const CancelButton = styled.button`
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 12px 24px;
  color: rgba(255, 255, 255, 0.8);
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.3);
  }
`;

function AdvancedResultsModal({ isOpen, onClose, type, data, editedItems, updateEditedItem, editClarifications, setEditClarifications, applyEditRecipe }) {
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
                  
                  {data.nutritionInfo && (
                    <SubSection>
                      <SubTitle>Nutrition Information</SubTitle>
                      <InsightDescription>{data.nutritionInfo}</InsightDescription>
                    </SubSection>
                  )}
                  
                  {data.healthBenefits && (
                    <SubSection>
                      <SubTitle>Health Benefits</SubTitle>
                      <InsightDescription>{data.healthBenefits}</InsightDescription>
                    </SubSection>
                  )}
                  
                  {data.regionalVariations && (
                    <SubSection>
                      <SubTitle>Regional Variations</SubTitle>
                      <InsightDescription>{data.regionalVariations}</InsightDescription>
                    </SubSection>
                  )}
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
                  <SwapOriginal>Currently: {swap.original}</SwapOriginal>
                  <SwapNew>Healthier Alternative: {swap.alternative}</SwapNew>
                  <SwapBenefits>
                    <div style={{ marginBottom: '8px' }}>
                      <strong>Health Benefits:</strong> {swap.benefits}
                    </div>
                    {swap.indianBenefit && (
                      <div style={{ color: '#805ad5' }}>
                        <strong>Cultural Benefits:</strong> {swap.indianBenefit}
                      </div>
                    )}
                  </SwapBenefits>
                </SwapInfo>
              </SwapItem>
            ))}
            <div style={{ marginTop: '20px', padding: '15px', background: 'rgba(255, 255, 255, 0.05)', borderRadius: '12px' }}>
              <p style={{ color: 'rgba(255, 255, 255, 0.8)', fontSize: '0.9rem', lineHeight: '1.6' }}>
                These alternatives are suggested based on traditional Indian nutrition principles while maintaining cultural authenticity.
              </p>
            </div>
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
                {/* Macro Balance Section */}
                <InsightCard>
                  <InsightTitle>
                    Macro Nutrient Balance
                    <span style={{
                      marginLeft: '10px',
                      padding: '4px 8px',
                      borderRadius: '12px',
                      fontSize: '0.8rem',
                      background: data.macroBalance.status === 'good' ? 'rgba(72, 187, 120, 0.2)' : 'rgba(237, 137, 54, 0.2)',
                      color: data.macroBalance.status === 'good' ? '#48bb78' : '#ed8936'
                    }}>
                      {data.macroBalance.status === 'good' ? 'Good' : 'Needs Improvement'}
                    </span>
                  </InsightTitle>
                  <InsightDescription>{data.macroBalance.details}</InsightDescription>
                  
                  {data.macroBalance.recommendations.length > 0 && (
                    <div style={{ marginTop: '10px' }}>
                      <strong style={{ color: '#90cdf4' }}>Recommendations:</strong>
                      <List>
                        {data.macroBalance.recommendations.map((rec, idx) => (
                          <ListItem key={idx}>{rec}</ListItem>
                        ))}
                      </List>
                    </div>
                  )}
                </InsightCard>

                {/* Micronutrients Section */}
                <InsightCard>
                  <InsightTitle>Micronutrient Analysis</InsightTitle>
                  
                  {data.micronutrients.highlights.length > 0 && (
                    <div style={{ marginBottom: '15px' }}>
                      <strong style={{ color: '#48bb78' }}>Highlights:</strong>
                      <List>
                        {data.micronutrients.highlights.map((highlight, idx) => (
                          <ListItem key={idx}>{highlight}</ListItem>
                        ))}
                      </List>
                    </div>
                  )}

                  {data.micronutrients.deficiencies.length > 0 && (
                    <div>
                      <strong style={{ color: '#f56565' }}>Areas for Improvement:</strong>
                      <List>
                        {data.micronutrients.deficiencies.map((deficiency, idx) => (
                          <ListItem key={idx}>{deficiency}</ListItem>
                        ))}
                      </List>
                    </div>
                  )}
                </InsightCard>

                {/* Health Benefits Section */}
                {data.healthBenefits.length > 0 && (
                  <InsightCard>
                    <InsightTitle>Health Benefits</InsightTitle>
                    <List>
                      {data.healthBenefits.map((benefit, idx) => (
                        <ListItem key={idx}>{benefit}</ListItem>
                      ))}
                    </List>
                  </InsightCard>
                )}

                {/* Concerns Section */}
                {data.concerns.length > 0 && (
                  <InsightCard>
                    <InsightTitle>Areas to Watch</InsightTitle>
                    <List>
                      {data.concerns.map((concern, idx) => (
                        <ListItem key={idx} style={{ color: '#f56565' }}>{concern}</ListItem>
                      ))}
                    </List>
                  </InsightCard>
                )}

                {/* Recommendations Section */}
                {data.recommendations.length > 0 && (
                  <InsightCard>
                    <InsightTitle>Personalized Recommendations</InsightTitle>
                    <List>
                      {data.recommendations.map((rec, idx) => (
                        <ListItem key={idx}>{rec}</ListItem>
                      ))}
                    </List>
                  </InsightCard>
                )}
              </>
            )}
          </>
        );

      case 'edit-recipe':
        return (
          <>
            <Title>
              <Edit3 size={24} />
              Edit Recipe Items
            </Title>
            <EditForm>
              {editedItems?.map((item, index) => (
                <EditItem key={index}>
                  <EditItemTitle>Item {index + 1}</EditItemTitle>
                  
                  <EditField>
                    <EditLabel>Food Name</EditLabel>
                    <EditInput
                      type="text"
                      value={item.name}
                      onChange={(e) => updateEditedItem(index, 'name', e.target.value)}
                      placeholder="Enter food name"
                    />
                  </EditField>
                  
                  <EditField>
                    <EditLabel>Quantity</EditLabel>
                    <EditInput
                      type="text"
                      value={item.quantity}
                      onChange={(e) => updateEditedItem(index, 'quantity', e.target.value)}
                      placeholder="e.g., 1 cup, 200g, 2 pieces"
                    />
                  </EditField>
                  
                  {item.originalName !== item.name && (
                    <div style={{ 
                      fontSize: '0.9rem', 
                      color: 'rgba(255, 255, 255, 0.6)',
                      fontStyle: 'italic'
                    }}>
                      Originally: {item.originalName}
                    </div>
                  )}
                </EditItem>
              ))}
              
              <EditItem>
                <EditItemTitle>Additional Notes</EditItemTitle>
                <EditField>
                  <EditLabel>Clarifications or special instructions</EditLabel>
                  <EditTextarea
                    value={editClarifications}
                    onChange={(e) => setEditClarifications(e.target.value)}
                    placeholder="Any additional clarifications about preparation, cooking method, or special ingredients..."
                  />
                </EditField>
              </EditItem>
            </EditForm>
            
            <EditActions>
              <CancelButton onClick={onClose}>
                Cancel
              </CancelButton>
              <EditButton onClick={applyEditRecipe}>
                <Edit3 size={16} />
                Apply Changes
              </EditButton>
            </EditActions>
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
  );
}

export default AdvancedResultsModal;