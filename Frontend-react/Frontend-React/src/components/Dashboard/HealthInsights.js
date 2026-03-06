import {
    ArcElement,
    CategoryScale,
    Chart as ChartJS,
    Legend,
    LinearScale,
    LineElement,
    PointElement,
    Title,
    Tooltip
} from 'chart.js';
import { motion } from 'framer-motion';
import {
    Activity,
    AlertTriangle,
    BarChart3,
    CheckCircle,
    RefreshCw,
    Target,
    TrendingUp
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { Doughnut, Line } from 'react-chartjs-2';
import styled from 'styled-components';
import { useApp } from '../../App';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

// Styled Components
const InsightsContainer = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 30px;
  margin-bottom: 30px;
`;

const InsightsHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
`;

const SectionTitle = styled.h2`
  font-size: 1.8rem;
  font-weight: 700;
  color: white;
  display: flex;
  align-items: center;
  gap: 15px;
  margin: 0;
`;

const TimeSelector = styled.div`
  display: flex;
  gap: 10px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 5px;
`;

const TimeButton = styled(motion.button)`
  background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'transparent'};
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'rgba(255, 255, 255, 0.1)'};
  }
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
`;

const StatCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
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
  }
`;

const StatHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
`;

const StatIcon = styled.div`
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: ${props => props.gradient};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: 700;
  color: white;
  margin-bottom: 5px;
`;

const StatLabel = styled.div`
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
`;

const StatChange = styled.div`
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.8rem;
  color: ${props => props.positive ? '#48bb78' : '#f56565'};
  margin-top: 8px;
`;

const ChartsGrid = styled.div`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;

  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const ChartCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 25px;
`;

const ChartTitle = styled.h3`
  color: white;
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
`;



const PieChart = styled.div`
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: conic-gradient(
    #48bb78 0deg 120deg,    /* Carbs - Green */
    #667eea 120deg 180deg,  /* Protein - Blue */
    #ed8936 180deg 220deg,  /* Fat - Orange */
    #38b2ac 220deg 240deg,  /* Fiber - Teal */
    #9f7aea 240deg 360deg   /* Other - Purple */
  );
  margin: 20px auto;
  position: relative;
  
  &::after {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 60%;
    height: 60%;
    background: rgba(30, 41, 59, 0.9);
    border-radius: 50%;
    transform: translate(-50%, -50%);
  }
`;

const PieLegend = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-top: 15px;
`;

const LegendItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.8);
`;

const LegendColor = styled.div`
  width: 12px;
  height: 12px;
  border-radius: 3px;
  background: ${props => props.color};
`;

const DeficiencySection = styled.div`
  background: rgba(255, 69, 69, 0.1);
  border: 1px solid rgba(255, 69, 69, 0.2);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
`;

const DeficiencyTitle = styled.h3`
  color: #ff6b6b;
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 10px;
`;

const DeficiencyList = styled.div`
  display: grid;
  gap: 10px;
`;

const DeficiencyItem = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 15px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.9);
`;

const DeficiencyValue = styled.span`
  color: ${props => props.severity === 'high' ? '#e53e3e' : '#ed8936'};
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 6px;
  background: ${props => props.severity === 'high' ? 'rgba(229, 62, 62, 0.2)' : 'rgba(237, 137, 54, 0.2)'};
  font-size: 0.8rem;
`;

const RefreshButton = styled(motion.button)`
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  padding: 8px 12px;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9rem;
  
  &:hover {
    background: rgba(255, 255, 255, 0.15);
  }
`;

const HealthInsights = ({ userId }) => {
  const { user, BASE_URL } = useApp();
  // Use the passed userId prop or fallback to user from context
  const activeUserId = userId || user?.id;
  const [timeRange, setTimeRange] = useState('7days');
  const [nutritionData, setNutritionData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (activeUserId) {
      fetchNutritionData();
    }
  }, [activeUserId, timeRange]);

  const fetchNutritionData = async () => {
    if (!activeUserId) return;
    
    setLoading(true);
    try {
      // Map timeRange to backend period format
      const periodMap = {
        '7days': '7d',
        '1month': '1m', 
        '3months': '3m'
      };
      
      const response = await fetch(`${BASE_URL}/dashboard/nutrition-insights/${activeUserId}?period=${periodMap[timeRange] || '7d'}`);
      if (response.ok) {
        const responseData = await response.json();
        const backendData = responseData.data; // Extract the data from the wrapped response
        
        console.log('Backend nutrition data:', backendData); // Debug log
        
        // Transform backend data to match component expectations
        const transformedData = {
          summary: {
            avgCalories: backendData.averages?.calories || 0,
            avgProtein: backendData.averages?.protein || 0,
            avgCarbs: backendData.averages?.carbs || 0,
            avgFat: backendData.averages?.fat || 0,
            avgFiber: backendData.averages?.fiber || 0,
            calorieChange: 0, // Will need historical data for trends
            proteinChange: 0,
            weightChange: 0,
            bodyFatChange: 0
          },
          macronutrients: backendData.macronutrients || { protein: 30, carbs: 40, fat: 30 },
          dailyTrend: backendData.daily_trend || [],
          deficiencies: backendData.deficiencies || [],
          stats: backendData.stats || {}
        };
        
        console.log('Transformed nutrition data:', transformedData); // Debug log
        setNutritionData(transformedData);
      } else {
        console.warn(`API request failed with status: ${response.status}`);
        const errorText = await response.text();
        console.warn('Error response:', errorText);
        setNutritionData(generateMockData());
      }
    } catch (error) {
      console.error("Failed to fetch nutrition data:", error);
      const periodMap = {
        '7days': '7d',
        '1month': '1m', 
        '3months': '3m'
      };
      console.error("Error details:", {
        message: error.message,
        stack: error.stack,
        activeUserId: activeUserId,
        timeRange: timeRange,
        baseUrl: BASE_URL,
        apiUrl: `${BASE_URL}/dashboard/nutrition-insights/${activeUserId}?period=${periodMap[timeRange] || '7d'}`
      });
      // Mock data for development
      setNutritionData(generateMockData());
    }
    setLoading(false);
  };

  const generateMockData = () => ({
    summary: {
      avgCalories: 2233,
      avgProtein: 128,
      avgCarbs: 210,
      avgFat: 67,
      avgFiber: 28,
      calorieChange: 5.2,
      proteinChange: -2.1,
      weightChange: 2.4,
      bodyFatChange: -1.0
    },
    macronutrients: {
      protein: 30,
      carbs: 45,
      fat: 25
    },
    deficiencies: [
      {
        nutrient: "Fiber",
        severity: "moderate",
        message: "Your fiber intake is 25% below recommended levels",
        recommendation: "Add more fruits, vegetables, whole grains, and legumes to your diet"
      },
      {
        nutrient: "Protein",
        severity: "high", 
        message: "You're getting 15% less protein than recommended",
        recommendation: "Consider adding lean meats, fish, eggs, or plant-based proteins to your meals"
      }
    ],
    dailyTrend: [
      { date: new Date().toISOString().split('T')[0], calories: 2100, protein: 120, carbs: 200, fat: 65 },
      { date: new Date(Date.now() - 86400000).toISOString().split('T')[0], calories: 2300, protein: 135, carbs: 220, fat: 70 },
      { date: new Date(Date.now() - 2*86400000).toISOString().split('T')[0], calories: 2200, protein: 125, carbs: 210, fat: 68 },
      { date: new Date(Date.now() - 3*86400000).toISOString().split('T')[0], calories: 2400, protein: 140, carbs: 225, fat: 75 },
      { date: new Date(Date.now() - 4*86400000).toISOString().split('T')[0], calories: 2150, protein: 118, carbs: 205, fat: 62 },
      { date: new Date(Date.now() - 5*86400000).toISOString().split('T')[0], calories: 2350, protein: 132, carbs: 215, fat: 72 },
      { date: new Date(Date.now() - 6*86400000).toISOString().split('T')[0], calories: 2250, protein: 128, carbs: 208, fat: 69 }
    ],
    stats: {
      total_meals: 42,
      avg_calories: 2233,
      calories_goal_achievement: 85.2,
      protein_intake: 128
    }
  });

  const data = nutritionData || generateMockData();

  return (
    <InsightsContainer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <InsightsHeader>
        <SectionTitle>
          <BarChart3 size={24} />
          Your Health Insights
        </SectionTitle>
        <div style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
          <TimeSelector>
            <TimeButton 
              active={timeRange === '7days'}
              onClick={() => setTimeRange('7days')}
            >
              7 Days
            </TimeButton>
            <TimeButton 
              active={timeRange === '1month'}
              onClick={() => setTimeRange('1month')}
            >
              1 Month
            </TimeButton>
            <TimeButton 
              active={timeRange === '3months'}
              onClick={() => setTimeRange('3months')}
            >
              3 Months
            </TimeButton>
          </TimeSelector>
          <RefreshButton
            onClick={fetchNutritionData}
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            disabled={loading}
          >
            <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
            Refresh
          </RefreshButton>
        </div>
      </InsightsHeader>

      {/* Key Stats */}
      <StatsGrid>
        <StatCard
          gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
          whileHover={{ scale: 1.02 }}
        >
          <StatHeader>
            <StatIcon gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
              <Target size={20} />
            </StatIcon>
          </StatHeader>
          <StatValue>{data.summary.avgCalories}</StatValue>
          <StatLabel>Avg Daily Calories</StatLabel>
          <StatChange positive={data.summary.calorieChange > 0}>
            <TrendingUp size={12} />
            {data.summary.calorieChange > 0 ? '+' : ''}{data.summary.calorieChange}% this {timeRange}
          </StatChange>
        </StatCard>

        <StatCard
          gradient="linear-gradient(135deg, #48bb78 0%, #38a169 100%)"
          whileHover={{ scale: 1.02 }}
        >
          <StatHeader>
            <StatIcon gradient="linear-gradient(135deg, #48bb78 0%, #38a169 100%)">
              <Activity size={20} />
            </StatIcon>
          </StatHeader>
          <StatValue>{data.summary.avgProtein}g</StatValue>
          <StatLabel>Avg Daily Protein</StatLabel>
          <StatChange positive={data.summary.proteinChange > 0}>
            <TrendingUp size={12} />
            {data.summary.proteinChange > 0 ? '+' : ''}{data.summary.proteinChange}% this {timeRange}
          </StatChange>
        </StatCard>

        <StatCard
          gradient="linear-gradient(135deg, #ed8936 0%, #dd6b20 100%)"
          whileHover={{ scale: 1.02 }}
        >
          <StatHeader>
            <StatIcon gradient="linear-gradient(135deg, #ed8936 0%, #dd6b20 100%)">
              <TrendingUp size={20} />
            </StatIcon>
          </StatHeader>
          <StatValue>77.6 kg</StatValue>
          <StatLabel>Current Weight</StatLabel>
          <StatChange positive={data.summary.weightChange > 0}>
            <TrendingUp size={12} />
            +{data.summary.weightChange}kg this month
          </StatChange>
        </StatCard>

        <StatCard
          gradient="linear-gradient(135deg, #38b2ac 0%, #319795 100%)"
          whileHover={{ scale: 1.02 }}
        >
          <StatHeader>
            <StatIcon gradient="linear-gradient(135deg, #38b2ac 0%, #319795 100%)">
              <CheckCircle size={20} />
            </StatIcon>
          </StatHeader>
          <StatValue>78%</StatValue>
          <StatLabel>Goal Progress</StatLabel>
          <StatChange positive={true}>
            <CheckCircle size={12} />
            On track
          </StatChange>
        </StatCard>
      </StatsGrid>

      {/* Charts */}
      <ChartsGrid>
        <ChartCard whileHover={{ scale: 1.01 }}>
          <ChartTitle>
            <TrendingUp size={20} />
            Daily Calorie Intake
          </ChartTitle>
          <div style={{ height: '250px', position: 'relative' }}>
            <Line
              data={{
                labels: data.dailyTrend.map(day => new Date(day.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })),
                datasets: [
                  {
                    label: 'Calories',
                    data: data.dailyTrend.map(day => day.calories),
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    fill: true,
                    tension: 0.4
                  }
                ]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    labels: {
                      color: 'rgba(255, 255, 255, 0.8)'
                    }
                  }
                },
                scales: {
                  x: {
                    ticks: {
                      color: 'rgba(255, 255, 255, 0.6)'
                    },
                    grid: {
                      color: 'rgba(255, 255, 255, 0.1)'
                    }
                  },
                  y: {
                    ticks: {
                      color: 'rgba(255, 255, 255, 0.6)'
                    },
                    grid: {
                      color: 'rgba(255, 255, 255, 0.1)'
                    }
                  }
                }
              }}
            />
          </div>
        </ChartCard>

        <ChartCard whileHover={{ scale: 1.01 }}>
          <ChartTitle>
            <Activity size={20} />
            Macronutrient Balance
          </ChartTitle>
          <div style={{ height: '250px', position: 'relative', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            <Doughnut
              data={{
                labels: ['Carbs', 'Protein', 'Fat'],
                datasets: [
                  {
                    data: [
                      data.macronutrients.carbs || 40,
                      data.macronutrients.protein || 30,
                      data.macronutrients.fat || 30
                    ],
                    backgroundColor: [
                      '#48bb78',
                      '#667eea',
                      '#ed8936'
                    ],
                    borderColor: [
                      '#48bb78',
                      '#667eea',
                      '#ed8936'
                    ],
                    borderWidth: 2
                  }
                ]
              }}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: {
                    position: 'bottom',
                    labels: {
                      color: 'rgba(255, 255, 255, 0.8)',
                      padding: 20,
                      usePointStyle: true
                    }
                  }
                }
              }}
            />
          </div>
        </ChartCard>
      </ChartsGrid>

      {/* Nutritional Deficiencies */}
      <DeficiencySection>
        <DeficiencyTitle>
          <AlertTriangle size={20} />
          Nutritional Deficiencies & Recommendations
        </DeficiencyTitle>
        <DeficiencyList>
          {Array.isArray(data.deficiencies) ? (
            data.deficiencies.length > 0 ? (
              data.deficiencies.map((deficiency, index) => (
                <DeficiencyItem key={index}>
                  <span>
                    {deficiency.nutrient}: {deficiency.message}
                  </span>
                  <DeficiencyValue severity={deficiency.severity}>
                    {deficiency.severity === 'high' ? 'High Priority' : 'Moderate'}
                  </DeficiencyValue>
                  <div style={{ fontSize: '0.9rem', color: 'rgba(255, 255, 255, 0.7)', marginTop: '8px' }}>
                    💡 {deficiency.recommendation}
                  </div>
                </DeficiencyItem>
              ))
            ) : (
              <DeficiencyItem>
                <span style={{ color: '#48bb78' }}>
                  <CheckCircle size={16} style={{ marginRight: '8px' }} />
                  Great! No major nutritional deficiencies detected.
                </span>
              </DeficiencyItem>
            )
          ) : (
            // Fallback for old format (object)
            Object.entries(data.deficiencies).map(([nutrient, info]) => (
              <DeficiencyItem key={nutrient}>
                <span>
                  {nutrient.replace('_', ' ').toUpperCase()}: {info.current}{info.unit} 
                  <span style={{ color: 'rgba(255, 255, 255, 0.6)' }}> (Target: {info.recommended}{info.unit})</span>
                </span>
                <DeficiencyValue>
                  -{Math.round(((info.recommended - info.current) / info.recommended) * 100)}%
                </DeficiencyValue>
              </DeficiencyItem>
            ))
          )}
        </DeficiencyList>
      </DeficiencySection>
    </InsightsContainer>
  );
};

export default HealthInsights;