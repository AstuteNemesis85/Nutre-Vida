import { motion } from 'framer-motion';
import {
  Calendar,
  Camera,
  History,
  RefreshCw,
  Save,
  User
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styled from 'styled-components';
import { useApp } from '../../App';
import HealthInsights from './HealthInsights';

const DashboardContainer = styled(motion.div)`
  min-height: 100vh;
  padding: 40px 20px;
  max-width: 1200px;
  margin: 0 auto;
`;

const WelcomeSection = styled(motion.div)`
  text-align: center;
  margin-bottom: 50px;
`;

const WelcomeTitle = styled.h1`
  font-family: 'Orbitron', monospace;
  font-size: 3rem;
  font-weight: 800;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #48bb78 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 10px;
  
  @media (max-width: 768px) {
    font-size: 2rem;
  }
`;

const WelcomeSubtitle = styled.p`
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 30px;
`;

const QuickActionsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
`;

const QuickActionCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 30px;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: ${props => props.gradient};
    opacity: 0.8;
  }
  
  &:hover {
    transform: translateY(-5px);
    border-color: rgba(255, 255, 255, 0.2);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
  }
`;

const ActionIcon = styled.div`
  width: 60px;
  height: 60px;
  border-radius: 16px;
  background: ${props => props.gradient};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin-bottom: 20px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.2);
`;

const ActionTitle = styled.h3`
  font-size: 1.3rem;
  font-weight: 700;
  color: white;
  margin-bottom: 10px;
  font-family: 'Orbitron', monospace;
`;

const ActionDescription = styled.p`
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
  font-size: 0.95rem;
`;

const PersonalizationSection = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 40px;
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

const FormGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
`;

const FormGroup = styled.div`
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
    border-color: rgba(102, 126, 234, 0.5);
    background: rgba(255, 255, 255, 0.15);
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
  
  option {
    background: #1a1a2e;
    color: white;
  }
`;

const SaveButton = styled(motion.button)`
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  border: none;
  border-radius: 12px;
  padding: 14px 28px;
  color: white;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.3s ease;
  font-family: 'Orbitron', monospace;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(72, 187, 120, 0.4);
  }
  
  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }
`;



const quickActions = [
  {
    title: 'Analyze Food',
    description: 'Upload a photo or describe your meal for instant nutrition analysis',
    icon: <Camera size={28} />,
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    path: '/analyze'
  },
  {
    title: 'Meal History',
    description: 'View your past analyses and track your nutrition journey',
    icon: <History size={28} />,
    gradient: 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)',
    path: '/history'
  },
  {
    title: 'Meal Plan',
    description: 'Get personalized meal plans based on your goals and preferences',
    icon: <Calendar size={28} />,
    gradient: 'linear-gradient(135deg, #ed8936 0%, #dd6b20 100%)',
    path: '/meal-plan'
  }
];

const Dashboard = () => {
  const navigate = useNavigate();
  const { user, connectionStatus, BASE_URL, showToast, updateUser } = useApp();
  const [profile, setProfile] = useState({
    gender: '',
    diet_preference: '',
    goal: '',
    activity: ''
  });

  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (user?.profile) {
      setProfile(user.profile);
    }
  }, [user]);

  const saveProfile = async () => {
    if (!user || connectionStatus === 'offline') {
      showToast("Cannot save profile while offline", 'error');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${BASE_URL}/users/${user.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile)
      });

      if (!response.ok) {
        throw new Error(`Profile update failed: ${response.status}`);
      }

      const updatedUser = await response.json();
      updateUser(updatedUser);
      
      showToast("Profile saved successfully!", 'success');
    } catch (error) {
      console.error("Profile save error:", error);
      showToast("Profile save failed: " + error.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setProfile(prev => ({ ...prev, [field]: value }));
  };

  return (
    <DashboardContainer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <WelcomeSection
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <WelcomeTitle>Welcome to Nutre-Vida</WelcomeTitle>
        <WelcomeSubtitle>
          Your AI-powered nutrition companion for a healthier lifestyle
        </WelcomeSubtitle>
      </WelcomeSection>

      <QuickActionsGrid>
        {quickActions.map((action, index) => (
          <QuickActionCard
            key={index}
            gradient={action.gradient}
            onClick={() => navigate(action.path)}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 + index * 0.1 }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <ActionIcon gradient={action.gradient}>
              {action.icon}
            </ActionIcon>
            <ActionTitle>{action.title}</ActionTitle>
            <ActionDescription>{action.description}</ActionDescription>
          </QuickActionCard>
        ))}
      </QuickActionsGrid>

      <PersonalizationSection
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.6 }}
      >
        <SectionTitle>
          <User size={24} />
          Personalization Settings
        </SectionTitle>
        
        <FormGrid>
          <FormGroup>
            <Label>Gender</Label>
            <Select
              value={profile.gender}
              onChange={(e) => handleInputChange('gender', e.target.value)}
            >
              <option value="">Select Gender</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </Select>
          </FormGroup>

          <FormGroup>
            <Label>Dietary Preference</Label>
            <Select
              value={profile.diet_preference}
              onChange={(e) => handleInputChange('diet_preference', e.target.value)}
            >
              <option value="">Select Dietary Preference</option>
              <option value="Vegetarian">Vegetarian</option>
              <option value="Non-Vegetarian">Non-Vegetarian</option>
              <option value="Vegan">Vegan</option>
              <option value="Eggetarian">Eggetarian</option>
            </Select>
          </FormGroup>

          <FormGroup>
            <Label>Goal</Label>
            <Select
              value={profile.goal}
              onChange={(e) => handleInputChange('goal', e.target.value)}
            >
              <option value="">Select Goal</option>
              <option value="Maintain Weight">Maintain Weight</option>
              <option value="Lose Weight">Lose Weight</option>
              <option value="Gain Weight">Gain Weight</option>
              <option value="Build Muscle">Build Muscle</option>
            </Select>
          </FormGroup>

          <FormGroup>
            <Label>Activity Level</Label>
            <Select
              value={profile.activity}
              onChange={(e) => handleInputChange('activity', e.target.value)}
            >
              <option value="">Select Activity Level</option>
              <option value="Sedentary">Sedentary (little/no exercise)</option>
              <option value="Lightly Active">Lightly Active (light exercise 1-3 days/week)</option>
              <option value="Moderately Active">Moderately Active (moderate exercise 3-5 days/week)</option>
              <option value="Active">Active (hard exercise 6-7 days/week)</option>
              <option value="Very Active">Very Active (very hard exercise/training)</option>
            </Select>
          </FormGroup>
        </FormGrid>

        <SaveButton
          onClick={saveProfile}
          disabled={isLoading}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
        >
          {isLoading ? <RefreshCw size={16} className="animate-spin" /> : <Save size={16} />}
          {isLoading ? 'Saving...' : 'Save Profile'}
        </SaveButton>
      </PersonalizationSection>

      <HealthInsights userId={user?.id} />
    </DashboardContainer>
  );
};

export default Dashboard;
