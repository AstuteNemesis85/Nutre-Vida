import React, { useState, useEffect } from 'react';
import styled from 'styled-components';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  History, 
  Calendar, 
  TrendingUp, 
  Eye, 
  Trash2, 
  Download,
  Filter,
  Search,
  BarChart3,
  PieChart,
  Activity,
  Target,
  Award,
  RefreshCw
} from 'lucide-react';
import { useApp } from '../../App';

const HistoryContainer = styled(motion.div)`
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
  background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
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

const StatsCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 30px;
  margin-bottom: 30px;
`;

const StatsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
`;

const StatItem = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 20px;
  text-align: center;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: ${props => props.gradient || 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)'};
  }
`;

const StatIcon = styled.div`
  width: 50px;
  height: 50px;
  border-radius: 12px;
  background: ${props => props.gradient || 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)'};
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin: 0 auto 15px;
`;

const StatValue = styled.div`
  font-size: 2rem;
  font-weight: 800;
  color: white;
  margin-bottom: 5px;
  font-family: 'Orbitron', monospace;
`;

const StatLabel = styled.div`
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.5px;
`;

const FiltersCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 30px;
  margin-bottom: 30px;
`;

const FiltersGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
`;

const FilterGroup = styled.div`
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
    border-color: rgba(72, 187, 120, 0.5);
    background: rgba(255, 255, 255, 0.15);
    box-shadow: 0 0 0 3px rgba(72, 187, 120, 0.1);
  }
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
    border-color: rgba(72, 187, 120, 0.5);
    background: rgba(255, 255, 255, 0.15);
    box-shadow: 0 0 0 3px rgba(72, 187, 120, 0.1);
  }
  
  option {
    background: #1a1a2e;
    color: white;
  }
`;

const MealsGrid = styled.div`
  display: grid;
  gap: 20px;
`;

const MealCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 30px;
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
  }
`;

const MealHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 15px;
`;

const MealInfo = styled.div`
  flex: 1;
`;

const MealTitle = styled.h3`
  color: white;
  font-size: 1.3rem;
  font-weight: 700;
  margin-bottom: 8px;
  font-family: 'Orbitron', monospace;
`;

const MealDate = styled.p`
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  margin-bottom: 5px;
`;

const MealSummary = styled.div`
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
`;

const SummaryItem = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  color: #68d391;
  font-weight: 600;
  font-size: 0.9rem;
`;

const MealActions = styled.div`
  display: flex;
  gap: 10px;
  flex-shrink: 0;
`;

const ActionButton = styled(motion.button)`
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 10px;
  padding: 8px 12px;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  transition: all 0.3s ease;
  
  &:hover {
    background: rgba(255, 255, 255, 0.15);
    color: white;
    transform: translateY(-1px);
  }
  
  &.danger:hover {
    background: rgba(245, 101, 101, 0.2);
    border-color: rgba(245, 101, 101, 0.3);
    color: #fc8181;
  }
`;

const MealDetails = styled(motion.div)`
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
`;

const ItemsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
`;

const ItemCard = styled.div`
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.1);
`;

const ItemName = styled.h4`
  color: white;
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 8px;
`;

const ItemDetails = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  font-size: 0.85rem;
`;

const ItemDetail = styled.div`
  display: flex;
  justify-content: space-between;
  color: rgba(255, 255, 255, 0.7);
  
  span:last-child {
    color: white;
    font-weight: 600;
  }
`;

const EmptyState = styled(motion.div)`
  text-align: center;
  padding: 60px 20px;
  color: rgba(255, 255, 255, 0.6);
`;

const EmptyIcon = styled.div`
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
  color: rgba(255, 255, 255, 0.3);
`;

const LoadingSpinner = styled.div`
  width: 40px;
  height: 40px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-top: 4px solid #48bb78;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 40px auto;
  
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`;

const MealHistory = () => {
  const [meals, setMeals] = useState([]);
  const [filteredMeals, setFilteredMeals] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedMeal, setExpandedMeal] = useState(null);
  const [filters, setFilters] = useState({
    search: '',
    dateFrom: '',
    dateTo: '',
    sortBy: 'newest'
  });
  const [stats, setStats] = useState({
    totalMeals: 0,
    avgCalories: 0,
    totalCalories: 0,
    avgProtein: 0
  });

  const { user, connectionStatus, BASE_URL, showToast } = useApp();

  useEffect(() => {
    if (user) {
      loadMealHistory();
    }
  }, [user]);

  useEffect(() => {
    applyFilters();
  }, [meals, filters]);

  const loadMealHistory = async () => {
    if (!user || connectionStatus === 'offline') {
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(`${BASE_URL}/users/${user.id}/meals`);

      if (!response.ok) {
        throw new Error(`History fetch failed: ${response.status}`);
      }

      const mealsData = await response.json();
      setMeals(mealsData);
      calculateStats(mealsData);
    } catch (error) {
      console.error("History error:", error);
      showToast("Failed to load meal history", 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const calculateStats = (mealsData) => {
    if (mealsData.length === 0) {
      setStats({ totalMeals: 0, avgCalories: 0, totalCalories: 0, avgProtein: 0 });
      return;
    }

    const totalCalories = mealsData.reduce((sum, meal) => 
      sum + (meal.analysis_data?.total_calories || 0), 0);
    const totalProtein = mealsData.reduce((sum, meal) => 
      sum + (meal.analysis_data?.total_protein || 0), 0);

    setStats({
      totalMeals: mealsData.length,
      avgCalories: Math.round(totalCalories / mealsData.length),
      totalCalories: Math.round(totalCalories),
      avgProtein: Math.round(totalProtein / mealsData.length)
    });
  };

  const applyFilters = () => {
    let filtered = [...meals];

    // Search filter
    if (filters.search) {
      filtered = filtered.filter(meal =>
        meal.analysis_data?.items?.some(item =>
          item.name.toLowerCase().includes(filters.search.toLowerCase())
        )
      );
    }

    // Date filters
    if (filters.dateFrom) {
      filtered = filtered.filter(meal =>
        new Date(meal.created_at) >= new Date(filters.dateFrom)
      );
    }

    if (filters.dateTo) {
      filtered = filtered.filter(meal =>
        new Date(meal.created_at) <= new Date(filters.dateTo)
      );
    }

    // Sort
    filtered.sort((a, b) => {
      switch (filters.sortBy) {
        case 'oldest':
          return new Date(a.created_at) - new Date(b.created_at);
        case 'calories-high':
          return (b.analysis_data?.total_calories || 0) - (a.analysis_data?.total_calories || 0);
        case 'calories-low':
          return (a.analysis_data?.total_calories || 0) - (b.analysis_data?.total_calories || 0);
        default: // newest
          return new Date(b.created_at) - new Date(a.created_at);
      }
    });

    setFilteredMeals(filtered);
  };

  const handleFilterChange = (field, value) => {
    setFilters(prev => ({ ...prev, [field]: value }));
  };

  const toggleMealDetails = (mealId) => {
    setExpandedMeal(expandedMeal === mealId ? null : mealId);
  };

  const deleteMeal = async (mealId) => {
    if (!window.confirm('Are you sure you want to delete this meal?')) return;

    try {
      // This would require a delete endpoint
      showToast("Delete functionality coming soon!", 'info');
    } catch (error) {
      showToast("Failed to delete meal", 'error');
    }
  };

  const exportHistory = () => {
    try {
      showToast("Export functionality coming soon!", 'info');
    } catch (error) {
      showToast("Failed to export history", 'error');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (!user) {
    return (
      <HistoryContainer
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <EmptyState>
          <EmptyIcon>
            <History size={40} />
          </EmptyIcon>
          <h3 style={{ color: 'white', marginBottom: '10px' }}>Please Login</h3>
          <p>You need to be logged in to view your meal history.</p>
        </EmptyState>
      </HistoryContainer>
    );
  }

  return (
    <HistoryContainer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <Header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <Title>Meal History</Title>
        <Subtitle>Track your nutrition journey and analyze your eating patterns</Subtitle>
      </Header>

      <StatsCard
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
      >
        <StatsGrid>
          <StatItem
            gradient="linear-gradient(135deg, #48bb78 0%, #38a169 100%)"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.4 }}
          >
            <StatIcon gradient="linear-gradient(135deg, #48bb78 0%, #38a169 100%)">
              <BarChart3 size={24} />
            </StatIcon>
            <StatValue>{stats.totalMeals}</StatValue>
            <StatLabel>Total Meals</StatLabel>
          </StatItem>

          <StatItem
            gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.5 }}
          >
            <StatIcon gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)">
              <Activity size={24} />
            </StatIcon>
            <StatValue>{stats.avgCalories}</StatValue>
            <StatLabel>Avg Calories</StatLabel>
          </StatItem>

          <StatItem
            gradient="linear-gradient(135deg, #ed8936 0%, #dd6b20 100%)"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.6 }}
          >
            <StatIcon gradient="linear-gradient(135deg, #ed8936 0%, #dd6b20 100%)">
              <Target size={24} />
            </StatIcon>
            <StatValue>{stats.totalCalories}</StatValue>
            <StatLabel>Total Calories</StatLabel>
          </StatItem>

          <StatItem
            gradient="linear-gradient(135deg, #f56565 0%, #e53e3e 100%)"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.3, delay: 0.7 }}
          >
            <StatIcon gradient="linear-gradient(135deg, #f56565 0%, #e53e3e 100%)">
              <Award size={24} />
            </StatIcon>
            <StatValue>{stats.avgProtein}g</StatValue>
            <StatLabel>Avg Protein</StatLabel>
          </StatItem>
        </StatsGrid>
      </StatsCard>

      <FiltersCard
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
      >
        <FiltersGrid>
          <FilterGroup>
            <Label>Search Meals</Label>
            <Input
              type="text"
              placeholder="Search by food name..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
            />
          </FilterGroup>

          <FilterGroup>
            <Label>From Date</Label>
            <Input
              type="date"
              value={filters.dateFrom}
              onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
            />
          </FilterGroup>

          <FilterGroup>
            <Label>To Date</Label>
            <Input
              type="date"
              value={filters.dateTo}
              onChange={(e) => handleFilterChange('dateTo', e.target.value)}
            />
          </FilterGroup>

          <FilterGroup>
            <Label>Sort By</Label>
            <Select
              value={filters.sortBy}
              onChange={(e) => handleFilterChange('sortBy', e.target.value)}
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="calories-high">Highest Calories</option>
              <option value="calories-low">Lowest Calories</option>
            </Select>
          </FilterGroup>
        </FiltersGrid>

        <div style={{ display: 'flex', gap: '15px', justifyContent: 'center', marginTop: '20px' }}>
          <ActionButton onClick={loadMealHistory}>
            <RefreshCw size={16} />
            Refresh
          </ActionButton>
          <ActionButton onClick={exportHistory}>
            <Download size={16} />
            Export
          </ActionButton>
        </div>
      </FiltersCard>

      {isLoading ? (
        <LoadingSpinner />
      ) : filteredMeals.length === 0 ? (
        <EmptyState
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.5 }}
        >
          <EmptyIcon>
            <History size={40} />
          </EmptyIcon>
          <h3 style={{ color: 'white', marginBottom: '10px' }}>No Meals Found</h3>
          <p>
            {meals.length === 0 
              ? "Start analyzing some food to build your meal history!"
              : "No meals match your current filters. Try adjusting your search criteria."
            }
          </p>
        </EmptyState>
      ) : (
        <MealsGrid>
          {filteredMeals.map((meal, index) => (
            <MealCard
              key={meal.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: index * 0.1 }}
            >
              <MealHeader>
                <MealInfo>
                  <MealTitle>Meal #{meal.id}</MealTitle>
                  <MealDate>{formatDate(meal.created_at)}</MealDate>
                  <MealSummary>
                    <SummaryItem>
                      <Activity size={16} />
                      {meal.analysis_data?.total_calories || 'N/A'} cal
                    </SummaryItem>
                    <SummaryItem>
                      <Target size={16} />
                      {meal.analysis_data?.items?.length || 0} items
                    </SummaryItem>
                  </MealSummary>
                </MealInfo>

                <MealActions>
                  <ActionButton onClick={() => toggleMealDetails(meal.id)}>
                    <Eye size={16} />
                    {expandedMeal === meal.id ? 'Hide' : 'View'}
                  </ActionButton>
                  <ActionButton 
                    className="danger"
                    onClick={() => deleteMeal(meal.id)}
                  >
                    <Trash2 size={16} />
                    Delete
                  </ActionButton>
                </MealActions>
              </MealHeader>

              <AnimatePresence>
                {expandedMeal === meal.id && (
                  <MealDetails
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <h4 style={{ color: 'white', marginBottom: '15px', fontFamily: 'Orbitron, monospace' }}>
                      Food Items
                    </h4>
                    
                    <ItemsGrid>
                      {meal.analysis_data?.items?.map((item, itemIndex) => (
                        <ItemCard key={itemIndex}>
                          <ItemName>{item.name}</ItemName>
                          <ItemDetails>
                            <ItemDetail>
                              <span>Quantity:</span>
                              <span>{item.quantity || 'N/A'}</span>
                            </ItemDetail>
                            <ItemDetail>
                              <span>Calories:</span>
                              <span>{item.calories || 'N/A'}</span>
                            </ItemDetail>
                            <ItemDetail>
                              <span>Protein:</span>
                              <span>{item.protein || 'N/A'}g</span>
                            </ItemDetail>
                            <ItemDetail>
                              <span>Carbs:</span>
                              <span>{item.carbs || 'N/A'}g</span>
                            </ItemDetail>
                            <ItemDetail>
                              <span>Fat:</span>
                              <span>{item.fat || 'N/A'}g</span>
                            </ItemDetail>
                            <ItemDetail>
                              <span>Confidence:</span>
                              <span>{item.confidence || 'N/A'}%</span>
                            </ItemDetail>
                          </ItemDetails>
                        </ItemCard>
                      ))}
                    </ItemsGrid>

                    {meal.analysis_data?.total_calories && (
                      <div style={{ 
                        background: 'linear-gradient(135deg, #48bb78 0%, #38a169 100%)',
                        borderRadius: '12px',
                        padding: '20px',
                        marginTop: '20px',
                        color: 'white'
                      }}>
                        <h4 style={{ marginBottom: '15px', fontFamily: 'Orbitron, monospace' }}>
                          Total Nutrition
                        </h4>
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: '15px' }}>
                          <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: '800' }}>
                              {meal.analysis_data.total_calories}
                            </div>
                            <div style={{ fontSize: '0.8rem', opacity: '0.9' }}>CALORIES</div>
                          </div>
                          <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: '800' }}>
                              {meal.analysis_data.total_protein || 'N/A'}
                            </div>
                            <div style={{ fontSize: '0.8rem', opacity: '0.9' }}>PROTEIN (G)</div>
                          </div>
                          <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: '800' }}>
                              {meal.analysis_data.total_carbs || 'N/A'}
                            </div>
                            <div style={{ fontSize: '0.8rem', opacity: '0.9' }}>CARBS (G)</div>
                          </div>
                          <div style={{ textAlign: 'center' }}>
                            <div style={{ fontSize: '1.5rem', fontWeight: '800' }}>
                              {meal.analysis_data.total_fat || 'N/A'}
                            </div>
                            <div style={{ fontSize: '0.8rem', opacity: '0.9' }}>FAT (G)</div>
                          </div>
                        </div>
                      </div>
                    )}
                  </MealDetails>
                )}
              </AnimatePresence>
            </MealCard>
          ))}
        </MealsGrid>
      )}
    </HistoryContainer>
  );
};

export default MealHistory;
