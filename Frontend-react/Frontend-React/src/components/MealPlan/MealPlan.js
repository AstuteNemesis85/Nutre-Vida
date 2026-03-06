import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Calendar, 
  ChefHat, 
  Clock, 
  Users, 
  Zap,
  RefreshCw,
  Download,
  Heart,
  Target,
  TrendingUp,
  Utensils,
  Apple,
  Coffee
} from 'lucide-react';
import { useApp } from '../../App';

const MealPlanContainer = styled(motion.div)`
  min-height: 100vh;
  padding: 40px 20px;
  max-width: 1200px;
  margin: 0 auto;
`;

const Header = styled(motion.div)`
  text-align: center;
  margin-bottom: 40px;
`;

const Title = styled.h1`
  font-family: 'Orbitron', monospace;
  font-size: 2.5rem;
  font-weight: 800;
  background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 10px;
  
  @media (max-width: 768px) {
    font-size: 2rem;
  }
`;

const Subtitle = styled.p`
  font-size: 1.1rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 30px;
`;

const PreferencesCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 30px;
`;

const SectionTitle = styled.h2`
  font-family: 'Orbitron', monospace;
  font-size: 1.8rem;
  font-weight: 700;
  color: white;
  margin-bottom: 30px;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const PreferencesGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
`;

const PreferenceGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 8px;
`;

const Label = styled.label`
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const Select = styled.select`
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 12px 16px;
  color: white;
  font-size: 0.95rem;
  outline: none;
  transition: all 0.3s ease;
  
  &:focus {
    border-color: rgba(237, 137, 54, 0.5);
    background: rgba(255, 255, 255, 0.15);
    box-shadow: 0 0 0 3px rgba(237, 137, 54, 0.1);
  }
  
  option {
    background: #1a1a2e;
    color: white;
  }
`;

const Input = styled.input`
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  padding: 12px 16px;
  color: white;
  font-size: 0.95rem;
  outline: none;
  transition: all 0.3s ease;
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
  
  &:focus {
    border-color: rgba(237, 137, 54, 0.5);
    background: rgba(255, 255, 255, 0.15);
    box-shadow: 0 0 0 3px rgba(237, 137, 54, 0.1);
  }
`;

const GenerateButton = styled(motion.button)`
  background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
  border: none;
  border-radius: 12px;
  padding: 16px 32px;
  color: white;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s ease;
  font-family: 'Orbitron', monospace;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin: 0 auto;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(237, 137, 54, 0.4);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;

const LoadingCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 60px 40px;
  text-align: center;
  margin-bottom: 30px;
`;

const LoadingSpinner = styled.div`
  width: 60px;
  height: 60px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-top: 4px solid #ed8936;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const LoadingText = styled.h3`
  color: white;
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 10px;
  font-family: 'Orbitron', monospace;
`;

const MealPlanCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 30px;
`;

const DayGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
`;

const DayCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 24px;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
  }
`;

const DayTitle = styled.h3`
  color: white;
  font-size: 1.3rem;
  font-weight: 700;
  margin-bottom: 20px;
  font-family: 'Orbitron', monospace;
  display: flex;
  align-items: center;
  gap: 10px;
`;

const MealSection = styled.div`
  margin-bottom: 20px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const MealTitle = styled.h4`
  color: #f6ad55;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const MealItem = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const MealName = styled.span`
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
`;

const MealCalories = styled.span`
  color: #48bb78;
  font-weight: 600;
  font-size: 0.9rem;
`;

const SummaryCard = styled(motion.div)`
  background: linear-gradient(135deg, #ed8936 0%, #dd6b20 100%);
  border-radius: 16px;
  padding: 24px;
  color: white;
  text-align: center;
`;

const SummaryTitle = styled.h3`
  font-family: 'Orbitron', monospace;
  font-size: 1.2rem;
  font-weight: 700;
  margin-bottom: 15px;
`;

const SummaryGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
`;

const SummaryItem = styled.div`
  text-align: center;
`;

const SummaryValue = styled.div`
  font-size: 1.5rem;
  font-weight: 800;
  margin-bottom: 5px;
`;

const SummaryLabel = styled.div`
  font-size: 0.8rem;
  opacity: 0.9;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
  flex-wrap: wrap;
`;

const SecondaryButton = styled(motion.button)`
  background: rgba(72, 187, 120, 0.2);
  border: 1px solid rgba(72, 187, 120, 0.3);
  border-radius: 12px;
  padding: 12px 24px;
  color: #68d391;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  font-family: 'Orbitron', monospace;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 0.9rem;
  
  &:hover {
    background: rgba(72, 187, 120, 0.3);
    transform: translateY(-1px);
  }
`;

const getMealIcon = (mealType) => {
  switch (mealType.toLowerCase()) {
    case 'breakfast':
      return <Coffee size={16} />;
    case 'lunch':
      return <Utensils size={16} />;
    case 'dinner':
      return <ChefHat size={16} />;
    case 'snack':
    case 'snacks':
      return <Apple size={16} />;
    default:
      return <Utensils size={16} />;
  }
};

const MealPlan = () => {
  const [preferences, setPreferences] = useState({
    days: '7',
    meals_per_day: '3',
    cuisine: '',
    dietary_restrictions: '',
    calorie_target: '',
    budget: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [mealPlan, setMealPlan] = useState(null);
  const { user, connectionStatus, BASE_URL, showToast } = useApp();

  useEffect(() => {
    // Load user profile preferences if available
    if (user?.profile) {
      setPreferences(prev => ({
        ...prev,
        dietary_restrictions: user.profile.diet_preference || '',
        calorie_target: getCalorieEstimate(user.profile) || ''
      }));
    }
  }, [user]);

  const getCalorieEstimate = (profile) => {
    // Simple calorie estimation based on profile
    if (profile.goal === 'Lose Weight') return '1800';
    if (profile.goal === 'Gain Weight') return '2500';
    if (profile.goal === 'Build Muscle') return '2200';
    return '2000';
  };

  const handleInputChange = (field, value) => {
    setPreferences(prev => ({ ...prev, [field]: value }));
  };

  const generateMealPlan = async () => {
    if (!user) {
      showToast("Please login first to generate a personalized meal plan", 'error');
      return;
    }

    if (connectionStatus === 'offline') {
      showToast("Cannot generate meal plan while offline", 'error');
      return;
    }

    setIsLoading(true);

    try {
      // Use the intelligent meal planner from agentic AI
      const planPreferences = {
        plan_type: preferences.days === '7' ? 'weekly' : 'custom',
        duration_days: parseInt(preferences.days),
        goals: {
          calorie_target: preferences.calorie_target ? parseInt(preferences.calorie_target) : null,
          dietary_restrictions: preferences.dietary_restrictions,
          cuisine_preference: preferences.cuisine,
          meals_per_day: parseInt(preferences.meals_per_day),
          budget: preferences.budget
        }
      };

      const response = await fetch(`${BASE_URL}/agentic/meal-plan/${user.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(planPreferences)
      });

      if (!response.ok) {
        // Fallback to basic meal plan generator
        const fallbackResponse = await fetch(`${BASE_URL}/recommendations/meal_plan/${user.id}`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...preferences, ...user.profile })
        });

        if (!fallbackResponse.ok) {
          throw new Error(`Meal plan generation failed: ${fallbackResponse.status}`);
        }

        const fallbackData = await fallbackResponse.json();
        let parsedPlan;
        if (typeof fallbackData.plan === 'string') {
          parsedPlan = parseMealPlanText(fallbackData.plan);
        } else {
          parsedPlan = fallbackData.plan;
        }
        
        setMealPlan(parsedPlan);
        showToast("Basic meal plan generated successfully!", 'success');
        return;
      }

      const data = await response.json();
      
      // Handle intelligent meal plan response
      if (data.meal_plan) {
        setMealPlan(data.meal_plan);
        showToast("Intelligent meal plan generated successfully!", 'success');
      } else if (data.plan) {
        // Parse the meal plan if it's a string
        let parsedPlan;
        if (typeof data.plan === 'string') {
          parsedPlan = parseMealPlanText(data.plan);
        } else {
          parsedPlan = data.plan;
        }
        
        setMealPlan(parsedPlan);
        showToast("Meal plan generated successfully!", 'success');
      } else {
        throw new Error("No meal plan data received");
      }
      
    } catch (error) {
      console.error("Meal plan error:", error);
      showToast("Failed to generate meal plan: " + error.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const parseMealPlanText = (planText) => {
    // Simple parser for text-based meal plans
    const days = [];
    const lines = planText.split('\n').filter(line => line.trim());
    
    let currentDay = null;
    let currentMeal = null;
    
    lines.forEach(line => {
      const trimmedLine = line.trim();
      
      // Check if it's a day header
      if (trimmedLine.match(/^(Day \d+|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)/i)) {
        if (currentDay) days.push(currentDay);
        currentDay = {
          day: trimmedLine,
          meals: {}
        };
        currentMeal = null;
      }
      // Check if it's a meal header
      else if (trimmedLine.match(/^(Breakfast|Lunch|Dinner|Snack)/i)) {
        currentMeal = trimmedLine.toLowerCase();
        if (currentDay && !currentDay.meals[currentMeal]) {
          currentDay.meals[currentMeal] = [];
        }
      }
      // It's a meal item
      else if (currentDay && currentMeal && trimmedLine.length > 0) {
        // Extract calories if present
        const calorieMatch = trimmedLine.match(/(\d+)\s*cal/i);
        const calories = calorieMatch ? calorieMatch[1] : null;
        const name = trimmedLine.replace(/\(\d+\s*cal\)/i, '').trim();
        
        currentDay.meals[currentMeal].push({
          name: name || trimmedLine,
          calories: calories
        });
      }
    });
    
    if (currentDay) days.push(currentDay);
    
    return { days };
  };

  const exportMealPlan = () => {
    if (!mealPlan) return;
    
    try {
      showToast("Export feature coming soon!", 'info');
    } catch (error) {
      showToast("Failed to export meal plan", 'error');
    }
  };

  const regeneratePlan = () => {
    setMealPlan(null);
    generateMealPlan();
  };

  return (
    <MealPlanContainer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <Header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <Title>Meal Plan Generator</Title>
        <Subtitle>Get personalized meal plans based on your goals and preferences</Subtitle>
      </Header>

      {!mealPlan && !isLoading && (
        <PreferencesCard
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.4 }}
        >
          <SectionTitle>
            <Target size={24} />
            Meal Plan Preferences
          </SectionTitle>
          
          <PreferencesGrid>
            <PreferenceGroup>
              <Label>Plan Duration</Label>
              <Select
                value={preferences.days}
                onChange={(e) => handleInputChange('days', e.target.value)}
              >
                <option value="3">3 Days</option>
                <option value="7">7 Days</option>
                <option value="14">14 Days</option>
                <option value="30">30 Days</option>
              </Select>
            </PreferenceGroup>

            <PreferenceGroup>
              <Label>Meals Per Day</Label>
              <Select
                value={preferences.meals_per_day}
                onChange={(e) => handleInputChange('meals_per_day', e.target.value)}
              >
                <option value="3">3 Meals</option>
                <option value="4">4 Meals</option>
                <option value="5">5 Meals</option>
                <option value="6">6 Meals</option>
              </Select>
            </PreferenceGroup>

            <PreferenceGroup>
              <Label>Cuisine Preference</Label>
              <Select
                value={preferences.cuisine}
                onChange={(e) => handleInputChange('cuisine', e.target.value)}
              >
                <option value="">Any Cuisine</option>
                <option value="Indian">Indian</option>
                <option value="Mediterranean">Mediterranean</option>
                <option value="Asian">Asian</option>
                <option value="American">American</option>
                <option value="Italian">Italian</option>
                <option value="Mexican">Mexican</option>
              </Select>
            </PreferenceGroup>

            <PreferenceGroup>
              <Label>Dietary Restrictions</Label>
              <Select
                value={preferences.dietary_restrictions}
                onChange={(e) => handleInputChange('dietary_restrictions', e.target.value)}
              >
                <option value="">No Restrictions</option>
                <option value="Vegetarian">Vegetarian</option>
                <option value="Vegan">Vegan</option>
                <option value="Gluten-Free">Gluten-Free</option>
                <option value="Dairy-Free">Dairy-Free</option>
                <option value="Keto">Keto</option>
                <option value="Paleo">Paleo</option>
              </Select>
            </PreferenceGroup>

            <PreferenceGroup>
              <Label>Daily Calorie Target</Label>
              <Input
                type="number"
                placeholder="e.g., 2000"
                value={preferences.calorie_target}
                onChange={(e) => handleInputChange('calorie_target', e.target.value)}
              />
            </PreferenceGroup>

            <PreferenceGroup>
              <Label>Budget (Optional)</Label>
              <Select
                value={preferences.budget}
                onChange={(e) => handleInputChange('budget', e.target.value)}
              >
                <option value="">Any Budget</option>
                <option value="Low">Low Budget</option>
                <option value="Medium">Medium Budget</option>
                <option value="High">High Budget</option>
              </Select>
            </PreferenceGroup>
          </PreferencesGrid>

          <GenerateButton
            onClick={generateMealPlan}
            disabled={isLoading}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
          >
            <ChefHat size={20} />
            Generate Meal Plan
          </GenerateButton>
        </PreferencesCard>
      )}

      <AnimatePresence>
        {isLoading && (
          <LoadingCard
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.3 }}
          >
            <LoadingSpinner />
            <LoadingText>Generating Your Meal Plan...</LoadingText>
            <p style={{ color: 'rgba(255, 255, 255, 0.7)', marginTop: '10px' }}>
              Creating personalized meals based on your preferences...
            </p>
          </LoadingCard>
        )}

        {mealPlan && (
          <MealPlanCard
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <SectionTitle>
              <Calendar size={24} />
              Your Personalized Meal Plan
            </SectionTitle>

            <DayGrid>
              {mealPlan.days?.map((day, index) => (
                <DayCard
                  key={index}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <DayTitle>
                    <Calendar size={20} />
                    {day.day}
                  </DayTitle>

                  {Object.entries(day.meals).map(([mealType, meals]) => (
                    <MealSection key={mealType}>
                      <MealTitle>
                        {getMealIcon(mealType)}
                        {mealType.charAt(0).toUpperCase() + mealType.slice(1)}
                      </MealTitle>
                      {meals.map((meal, mealIndex) => (
                        <MealItem key={mealIndex}>
                          <MealName>{meal.name}</MealName>
                          {meal.calories && (
                            <MealCalories>{meal.calories} cal</MealCalories>
                          )}
                        </MealItem>
                      ))}
                    </MealSection>
                  ))}
                </DayCard>
              ))}

              {/* Summary Card */}
              <SummaryCard
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: (mealPlan.days?.length || 0) * 0.1 }}
              >
                <SummaryTitle>Plan Summary</SummaryTitle>
                <SummaryGrid>
                  <SummaryItem>
                    <SummaryValue>{preferences.days}</SummaryValue>
                    <SummaryLabel>Days</SummaryLabel>
                  </SummaryItem>
                  <SummaryItem>
                    <SummaryValue>{preferences.meals_per_day}</SummaryValue>
                    <SummaryLabel>Meals/Day</SummaryLabel>
                  </SummaryItem>
                  <SummaryItem>
                    <SummaryValue>{preferences.calorie_target || '2000'}</SummaryValue>
                    <SummaryLabel>Target Cal</SummaryLabel>
                  </SummaryItem>
                  <SummaryItem>
                    <SummaryValue>{mealPlan.days?.length || 0}</SummaryValue>
                    <SummaryLabel>Total Days</SummaryLabel>
                  </SummaryItem>
                </SummaryGrid>
              </SummaryCard>
            </DayGrid>

            <ActionButtons>
              <GenerateButton
                onClick={regeneratePlan}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <RefreshCw size={16} />
                Regenerate Plan
              </GenerateButton>
              
              <SecondaryButton
                onClick={exportMealPlan}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Download size={16} />
                Export Plan
              </SecondaryButton>
            </ActionButtons>
          </MealPlanCard>
        )}
      </AnimatePresence>
    </MealPlanContainer>
  );
};

export default MealPlan;
