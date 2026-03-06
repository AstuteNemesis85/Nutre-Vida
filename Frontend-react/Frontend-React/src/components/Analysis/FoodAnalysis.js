import { AnimatePresence, motion } from 'framer-motion';
import {
  AlertCircle,
  Camera,
  CheckCircle,
  ChefHat,
  Download,
  Edit3,
  Lightbulb,
  RefreshCw,
  Type,
  Upload,
  Zap
} from 'lucide-react';
import { useRef, useState } from 'react';
import styled from 'styled-components';
import { useApp } from '../../App';
import AdvancedResultsModal from './AdvancedResultsModal.jsx';

const AnalysisContainer = styled(motion.div)`
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
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

const TabContainer = styled.div`
  display: flex;
  justify-content: center;
  margin-bottom: 40px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 16px;
  padding: 8px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
`;

const Tab = styled(motion.button)`
  background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'transparent'};
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  color: ${props => props.active ? 'white' : 'rgba(255, 255, 255, 0.7)'};
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  transition: all 0.3s ease;
  font-family: 'Orbitron', monospace;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 0.9rem;
  
  &:hover {
    color: white;
    background: ${props => props.active ? 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)' : 'rgba(255, 255, 255, 0.1)'};
  }
`;

const AnalysisCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 30px;
`;

const UploadArea = styled(motion.div)`
  border: 2px dashed rgba(102, 126, 234, 0.3);
  border-radius: 16px;
  padding: 60px 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(102, 126, 234, 0.05);
  position: relative;
  overflow: hidden;
  
  &:hover {
    border-color: rgba(102, 126, 234, 0.5);
    background: rgba(102, 126, 234, 0.1);
    transform: translateY(-2px);
  }
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
    transition: left 0.5s;
  }
  
  &:hover::before {
    left: 100%;
  }
`;

const UploadIcon = styled.div`
  width: 80px;
  height: 80px;
  border-radius: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  margin: 0 auto 20px;
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
`;

const UploadText = styled.h3`
  color: white;
  font-size: 1.3rem;
  font-weight: 600;
  margin-bottom: 10px;
  font-family: 'Orbitron', monospace;
`;

const UploadSubtext = styled.p`
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.95rem;
  line-height: 1.5;
`;

const HiddenInput = styled.input`
  display: none;
`;

const ImagePreview = styled(motion.div)`
  margin-top: 30px;
  text-align: center;
`;

const PreviewImage = styled.img`
  max-width: 100%;
  max-height: 400px;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  border: 2px solid rgba(255, 255, 255, 0.1);
`;

const TextInputArea = styled.div`
  margin-bottom: 30px;
`;

const TextArea = styled.textarea`
  width: 100%;
  min-height: 120px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 16px;
  padding: 20px;
  color: white;
  font-size: 1rem;
  outline: none;
  transition: all 0.3s ease;
  resize: vertical;
  font-family: 'Inter', sans-serif;
  
  &::placeholder {
    color: rgba(255, 255, 255, 0.5);
  }
  
  &:focus {
    border-color: rgba(102, 126, 234, 0.5);
    background: rgba(255, 255, 255, 0.15);
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
`;

const ActionButton = styled(motion.button)`
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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
  margin: 20px auto 0;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
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
  border-top: 4px solid #667eea;
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

const QuestionsCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 30px;
`;

const QuestionItem = styled.div`
  margin-bottom: 25px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const QuestionLabel = styled.label`
  display: block;
  color: white;
  font-weight: 600;
  margin-bottom: 10px;
  font-size: 1rem;
`;

const QuestionInput = styled.input`
  width: 100%;
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
    border-color: rgba(102, 126, 234, 0.5);
    background: rgba(255, 255, 255, 0.15);
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 15px;
  justify-content: center;
  margin-top: 30px;
  flex-wrap: wrap;
`;

const SecondaryButton = styled(motion.button)`
  background: rgba(237, 137, 54, 0.2);
  border: 1px solid rgba(237, 137, 54, 0.3);
  border-radius: 12px;
  padding: 12px 24px;
  color: #f6ad55;
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
    background: rgba(237, 137, 54, 0.3);
    transform: translateY(-1px);
  }
`;

const ResultsCard = styled(motion.div)`
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 30px;
`;

const ResultsGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
`;

const ResultItem = styled(motion.div)`
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
    background: ${props => props.gradient || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'};
  }
`;

const ItemTitle = styled.h3`
  color: white;
  font-size: 1.2rem;
  font-weight: 700;
  margin-bottom: 15px;
  font-family: 'Orbitron', monospace;
`;

const ItemQuantity = styled.p`
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 15px;
  font-weight: 500;
`;

const ConfidenceBar = styled.div`
  background: rgba(255, 255, 255, 0.1);
  height: 6px;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 15px;
`;

const ConfidenceFill = styled.div`
  height: 100%;
  background: linear-gradient(90deg, #48bb78 0%, #38a169 100%);
  width: ${props => props.confidence}%;
  transition: width 0.5s ease;
`;

const NutritionGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
`;

const NutritionItem = styled.div`
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  
  &:last-child {
    border-bottom: none;
  }
`;

const NutritionLabel = styled.span`
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
`;

const NutritionValue = styled.span`
  color: white;
  font-weight: 600;
  font-size: 0.9rem;
`;

const FoodAnalysis = () => {
  const [activeTab, setActiveTab] = useState('image');
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [textInput, setTextInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [questions, setQuestions] = useState([]);
  const [answers, setAnswers] = useState({});
  const [results, setResults] = useState(null);
  const [currentStep, setCurrentStep] = useState('input'); // input, loading, questions, results
  const [modalType, setModalType] = useState(null);
  const [modalData, setModalData] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const fileInputRef = useRef(null);
  
  const { user, sessionId, connectionStatus, BASE_URL, showToast, initSession } = useApp();

  const handleImageSelect = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      showToast("Please select a valid image file", 'error');
      return;
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      showToast("Image too large. Please select an image smaller than 10MB", 'error');
      return;
    }

    setSelectedImage(file);
    
    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setImagePreview(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  const uploadAndAnalyzeImage = async () => {
    if (!selectedImage) {
      showToast("Please select an image first", 'error');
      return;
    }

    if (connectionStatus === 'offline') {
      showToast("Cannot analyze while offline", 'error');
      return;
    }

    setIsLoading(true);
    setCurrentStep('loading');

    try {
      // Ensure we have a session
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        const success = await initSession();
        if (!success) return;
        currentSessionId = sessionId;
      }

      // Upload image
      const formData = new FormData();
      formData.append("file", selectedImage);

      const uploadResponse = await fetch(`${BASE_URL}/analysis/upload/${currentSessionId}`, {
        method: "POST",
        body: formData
      });

      if (!uploadResponse.ok) {
        throw new Error('Upload failed: ' + uploadResponse.status);
      }

      // Analyze image
      let analyzeUrl = `${BASE_URL}/analysis/analyze/${currentSessionId}`;
      if (user) analyzeUrl += `?user_id=${user.id}`;

      const analyzeResponse = await fetch(analyzeUrl, { method: "POST" });

      if (!analyzeResponse.ok) {
        throw new Error('Analysis failed: ' + analyzeResponse.status);
      }

      const data = await analyzeResponse.json();
      handleAnalysisResponse(data);

    } catch (error) {
      console.error("Analysis error:", error);
      showToast("Analysis failed: " + error.message, 'error');
      setCurrentStep('input');
    } finally {
      setIsLoading(false);
    }
  };

  const analyzeText = async () => {
    if (!textInput.trim()) {
      showToast("Please enter some food items first", 'error');
      return;
    }

    if (connectionStatus === 'offline') {
      showToast("Cannot analyze while offline", 'error');
      return;
    }

    setIsLoading(true);
    setCurrentStep('loading');

    try {
      // Ensure we have a session
      let currentSessionId = sessionId;
      if (!currentSessionId) {
        const success = await initSession();
        if (!success) return;
        currentSessionId = sessionId;
      }

      let url = `${BASE_URL}/analysis/analyze_text/${currentSessionId}`;
      if (user) url += `?user_id=${user.id}`;

      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: textInput })
      });

      if (!response.ok) {
        throw new Error('Text analysis failed: ' + response.status);
      }

      const data = await response.json();
      handleAnalysisResponse(data);

    } catch (error) {
      console.error("Text analysis error:", error);
      showToast("Text analysis failed: " + error.message, 'error');
      setCurrentStep('input');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAnalysisResponse = (data) => {
    if (data.questions && data.questions.length > 0) {
      setQuestions(data.questions);
      setAnswers({});
      setCurrentStep('questions');
    } else if (data.data && data.data.analysis_data) {
      setResults(data.data);
      setCurrentStep('results');
    } else {
      showToast("Analysis completed but no data received", 'error');
      setCurrentStep('input');
    }
  };

  const submitAnswers = async () => {
    const answerValues = questions.map((_, index) => answers[index] || '');
    
    if (answerValues.some(answer => !answer.trim())) {
      showToast("Please answer all questions before submitting", 'error');
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${BASE_URL}/analysis/refine/${sessionId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(answerValues)
      });

      if (!response.ok) {
        throw new Error(`Refinement failed: ${response.status}`);
      }

      const data = await response.json();
      setResults(data.data);
      setCurrentStep('results');
    } catch (error) {
      console.error("Refinement error:", error);
      showToast("Failed to refine analysis: " + error.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const skipQuestions = async () => {
    setIsLoading(true);

    try {
      const response = await fetch(`${BASE_URL}/analysis/skip_clarification/${sessionId}`, {
        method: "POST",
        headers: { 'Content-Type': 'application/json' }
      });

      if (!response.ok) {
        throw new Error(`Skip failed: ${response.status}`);
      }

      // Get results from session
      const resultsResponse = await fetch(`${BASE_URL}/analysis/results/${sessionId}`);
      if (resultsResponse.ok) {
        const resultsData = await resultsResponse.json();
        setResults({ analysis_data: resultsData });
        setCurrentStep('results');
      }
    } catch (error) {
      console.error("Skip error:", error);
      showToast("Failed to skip questions: " + error.message, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const startNewAnalysis = () => {
    setCurrentStep('input');
    setSelectedImage(null);
    setImagePreview(null);
    setTextInput('');
    setQuestions([]);
    setAnswers({});
    setResults(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const generateRecipe = async (analysisData) => {
    if (connectionStatus === 'offline') {
      showToast("Cannot generate recipe while offline", 'error');
      return;
    }

    try {
      showToast("Generating recipe...", 'info');
      
      const response = await fetch(`${BASE_URL}/recommendations/recipe`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(analysisData)
      });

      if (!response.ok) {
        throw new Error(`Recipe generation failed: ${response.status}`);
      }

      const data = await response.json();
      
      if (!data || !data.recipe) {
        throw new Error('No recipe data received from server');
      }
      
      // Parse the markdown response
      const recipeText = data.recipe;
      console.log('Raw recipe text:', recipeText); // Debug logging
      
      // Initialize default recipe structure
      const recipeData = {
        title: 'Generated Recipe',
        ingredients: [],
        instructions: [],
        nutritionInfo: '',
        healthBenefits: '',
        regionalVariations: ''
      };

      try {
        // Extract title
        const titleMatch = recipeText.match(/##\s*([^\n]+)/);
        if (titleMatch) {
          recipeData.title = titleMatch[1].trim();
        }

        // Extract ingredients
        const ingredientsMatch = recipeText.match(/###\s*Ingredients[\s\S]*?(?=###|$)/);
        if (ingredientsMatch) {
          recipeData.ingredients = ingredientsMatch[0]
            .replace(/###\s*Ingredients/, '')
            .trim()
            .split('\n')
            .filter(line => line.trim())
            .map(line => line.replace(/^[\s-]*/, '').trim());
        }

        // Extract instructions
        const instructionsMatch = recipeText.match(/###\s*Instructions[\s\S]*?(?=###|$)/);
        if (instructionsMatch) {
          recipeData.instructions = instructionsMatch[0]
            .replace(/###\s*Instructions/, '')
            .trim()
            .split('\n')
            .filter(line => line.trim())
            .map(line => line.replace(/^[\s\d.)-]*/, '').trim());
        }

        // Extract nutrition info
        const nutritionMatch = recipeText.match(/###\s*Nutrition Info[\s\S]*?(?=###|$)/);
        if (nutritionMatch) {
          recipeData.nutritionInfo = nutritionMatch[0]
            .replace(/###\s*Nutrition Info/, '')
            .trim();
        }

        // Extract health benefits
        const benefitsMatch = recipeText.match(/###\s*Health Benefits[\s\S]*?(?=###|$)/);
        if (benefitsMatch) {
          recipeData.healthBenefits = benefitsMatch[0]
            .replace(/###\s*Health Benefits/, '')
            .trim();
        }

        // Extract regional variations
        const variationsMatch = recipeText.match(/###\s*Regional Variations[\s\S]*?(?=###|$)/);
        if (variationsMatch) {
          recipeData.regionalVariations = variationsMatch[0]
            .replace(/###\s*Regional Variations/, '')
            .trim();
        }
      } catch (parseError) {
        console.error('Error parsing recipe:', parseError);
      }      // Ensure all arrays exist even if empty
      if (!Array.isArray(recipeData.ingredients)) recipeData.ingredients = [];
      if (!Array.isArray(recipeData.instructions)) recipeData.instructions = [];
      
      // Debug logging
      console.log('Recipe Data:', recipeData);

      showToast("Recipe generated successfully!", 'success');
      setModalData(recipeData);
      setModalType('recipe');
      setIsModalOpen(true);
      
    } catch (error) {
      console.error("Recipe generation error:", error);
      showToast("Failed to generate recipe: " + error.message, 'error');
      
      // Set empty recipe data as fallback
      setModalData({
        title: 'Recipe Generation Failed',
        ingredients: [],
        instructions: [],
        nutritionInfo: 'Unable to generate nutrition information',
        healthBenefits: 'Unable to generate health benefits',
        regionalVariations: ''
      });
      setModalType('recipe');
      setIsModalOpen(true);
    }
  };

  // Helper function to safely convert values to strings
  const _validateAndStringify = (value, fallback = 'Not specified') => {
    if (typeof value === 'string' && value.trim() !== '') {
      return value.trim();
    }
    if (typeof value === 'object' && value !== null) {
      // If it's an object, try to extract a meaningful string
      if (value.name) return String(value.name);
      if (value.title) return String(value.title);
      if (value.description) return String(value.description);
      // Otherwise stringify the object
      try {
        return JSON.stringify(value);
      } catch (e) {
        return fallback;
      }
    }
    if (value !== null && value !== undefined) {
      return String(value);
    }
    return fallback;
  };

  const getHealthySwaps = async (analysisData) => {
    if (connectionStatus === 'offline') {
      showToast("Cannot get healthy swaps while offline", 'error');
      return;
    }

    try {
      showToast("Finding healthy alternatives...", 'info');
      
      const response = await fetch(`${BASE_URL}/recommendations/swaps`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(analysisData)
      });

      if (!response.ok) {
        throw new Error(`Healthy swaps failed: ${response.status}`);
      }

      const data = await response.json();
      
      // Validate the response structure
      if (!data || !Array.isArray(data.swaps)) {
        throw new Error('Invalid response format: missing swaps array');
      }
      
      if (data.swaps.length === 0) {
        throw new Error('No healthy swaps available for this meal');
      }
      
      showToast("Healthy swaps found!", 'success');
      const formattedSwaps = data.swaps.map((swap, index) => {
        // Ensure swap is an object
        if (typeof swap !== 'object' || swap === null) {
          console.error(`Invalid swap at index ${index}:`, swap);
          return {
            original: 'Unknown item',
            alternative: 'Healthier option',
            benefits: 'Better nutrition profile',
            indianBenefit: 'Culturally appropriate'
          };
        }
        
        return {
          original: _validateAndStringify(swap.original, 'Current food item'),
          alternative: _validateAndStringify(swap.swap, 'Healthier alternative'),
          benefits: _validateAndStringify(swap.reason, 'Better nutritional profile'),
          indianBenefit: _validateAndStringify(swap.indian_benefit, 'Culturally appropriate choice')
        };
      });
      
      setModalData(formattedSwaps);
      setModalType('swaps');
      setIsModalOpen(true);
      
    } catch (error) {
      console.error("Healthy swaps error:", error);
      showToast("Failed to get healthy swaps: " + error.message, 'error');
    }
  };

  const getNutritionInsights = async (analysisData) => {
    if (connectionStatus === 'offline') {
      showToast("Cannot get nutrition insights while offline", 'error');
      return;
    }

    try {
      showToast("Analyzing nutrition insights...", 'info');
      
      const response = await fetch(`${BASE_URL}/recommendations/nutrition-insights`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(analysisData)
      });

      if (!response.ok) {
        throw new Error(`Nutrition insights failed: ${response.status}`);
      }

      const data = await response.json();
      
      // Check if the response contains an error
      if (data.error) {
        throw new Error(data.error);
      }
      
      // Check if macro_balance exists before accessing its properties
      if (!data.macro_balance) {
        throw new Error('Invalid response structure: missing macro_balance data');
      }
      
      showToast("Nutrition insights ready!", 'success');
      setModalData({
        macroBalance: {
          status: data.macro_balance.status || 'unknown',
          details: data.macro_balance.details || 'No details available',
          recommendations: data.macro_balance.recommendations || []
        },
        micronutrients: data.micronutrients || { highlights: [], deficiencies: [] },
        healthBenefits: data.health_benefits || [],
        concerns: data.concerns || [],
        recommendations: data.recommendations || []
      });
      setModalType('insights');
      setIsModalOpen(true);
      
    } catch (error) {
      console.error("Nutrition insights error:", error);
      showToast("Failed to get nutrition insights: " + error.message, 'error');
    }
  };

  // Edit Recipe functionality
  const [editedItems, setEditedItems] = useState([]);
  const [editClarifications, setEditClarifications] = useState('');

  const openEditRecipe = (analysisData) => {
    // Initialize edit state with current items
    const itemsToEdit = analysisData.items?.map(item => ({
      ...item,
      originalName: item.name,
      originalQuantity: item.quantity
    })) || [];
    
    setEditedItems(itemsToEdit);
    setEditClarifications('');
    setModalType('edit-recipe');
    setIsModalOpen(true);
  };

  const updateEditedItem = (index, field, value) => {
    const updated = [...editedItems];
    updated[index][field] = value;
    setEditedItems(updated);
  };

  const applyEditRecipe = async () => {
    if (connectionStatus === 'offline') {
      showToast("Cannot apply recipe edits while offline", 'error');
      return;
    }

    try {
      showToast("Reanalyzing with Gemini AI...", 'info');
      
      // Prepare the edited items for Gemini reanalysis
      const requestData = {
        edited_items: editedItems.map(item => ({
          name: item.name,
          quantity: item.quantity
        })),
        clarifications: editClarifications
      };

      // Send edited food items to Gemini for complete reanalysis
      const response = await fetch(`${BASE_URL}/recommendations/reanalyze-edited-items`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        throw new Error(`Failed to reanalyze with Gemini: ${response.status}`);
      }

      const data = await response.json();
      
      // Ensure the response has the expected structure with proper totals
      let reanalyzedData = data;
      
      // Validate and enhance the Gemini response
      if (data.items && Array.isArray(data.items)) {
        // Calculate totals to ensure accuracy
        const totalCalories = data.items.reduce((sum, item) => sum + (parseFloat(item.calories) || 0), 0);
        const totalProtein = data.items.reduce((sum, item) => sum + (parseFloat(item.protein) || 0), 0);
        const totalCarbs = data.items.reduce((sum, item) => sum + (parseFloat(item.carbs) || 0), 0);
        const totalFat = data.items.reduce((sum, item) => sum + (parseFloat(item.fat) || 0), 0);
        
        // Create enhanced structure with Gemini-analyzed data
        reanalyzedData = {
          items: data.items,
          total_calories: data.total_calories || totalCalories,
          total_protein: data.total_protein || totalProtein,
          total_carbs: data.total_carbs || totalCarbs,
          total_fat: data.total_fat || totalFat,
          // Preserve any additional fields from Gemini
          ...data
        };
        
        // Add confidence scores if missing (since these are edited items)
        reanalyzedData.items = reanalyzedData.items.map(item => ({
          ...item,
          confidence: item.confidence || 95 // High confidence for user-edited items
        }));
      }
      
      // Update results with Gemini's reanalysis
      setResults({ analysis_data: reanalyzedData });
      setIsModalOpen(false);
      showToast("Recipe updated with fresh Gemini analysis!", 'success');
      
    } catch (error) {
      console.error("Edit recipe reanalysis error:", error);
      showToast("Failed to reanalyze with Gemini: " + error.message, 'error');
    }
  };

  const exportPDF = () => {
    if (!results) return;
    
    try {
      // This would require jsPDF to be imported
      showToast("PDF export feature coming soon!", 'info');
    } catch (error) {
      showToast("Failed to export PDF", 'error');
    }
  };

  return (
    <AnalysisContainer
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
    >
      <Header
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <Title>Food Analysis</Title>
        <Subtitle>Upload an image or describe your food for instant nutrition analysis</Subtitle>
      </Header>

      {currentStep === 'input' && (
        <>
          <TabContainer>
            <Tab
              active={activeTab === 'image'}
              onClick={() => setActiveTab('image')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Camera size={18} />
              Image Upload
            </Tab>
            <Tab
              active={activeTab === 'text'}
              onClick={() => setActiveTab('text')}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Type size={18} />
              Text Input
            </Tab>
          </TabContainer>

          <AnalysisCard
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <AnimatePresence mode="wait">
              {activeTab === 'image' ? (
                <motion.div
                  key="image"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{ duration: 0.3 }}
                >
                  <UploadArea
                    onClick={() => fileInputRef.current?.click()}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <UploadIcon>
                      <Upload size={32} />
                    </UploadIcon>
                    <UploadText>Upload Food Image</UploadText>
                    <UploadSubtext>
                      Click to select an image or drag and drop<br />
                      Supports JPG, PNG, WebP (max 10MB)
                    </UploadSubtext>
                  </UploadArea>
                  
                  <HiddenInput
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleImageSelect}
                  />

                  <AnimatePresence>
                    {imagePreview && (
                      <ImagePreview
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        transition={{ duration: 0.3 }}
                      >
                        <PreviewImage src={imagePreview} alt="Food preview" />
                        <ActionButton
                          onClick={uploadAndAnalyzeImage}
                          whileHover={{ scale: 1.05 }}
                          whileTap={{ scale: 0.95 }}
                        >
                          <Zap size={20} />
                          Analyze Image
                        </ActionButton>
                      </ImagePreview>
                    )}
                  </AnimatePresence>
                </motion.div>
              ) : (
                <motion.div
                  key="text"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ duration: 0.3 }}
                >
                  <TextInputArea>
                    <TextArea
                      value={textInput}
                      onChange={(e) => setTextInput(e.target.value)}
                      placeholder="Enter dishes with quantities (e.g., 'chicken biryani 200g, mixed vegetable curry 150g, naan 2 pieces')"
                    />
                  </TextInputArea>
                  
                  <ActionButton
                    onClick={analyzeText}
                    disabled={!textInput.trim()}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <Zap size={20} />
                    Analyze Text
                  </ActionButton>
                </motion.div>
              )}
            </AnimatePresence>
          </AnalysisCard>
        </>
      )}

      <AnimatePresence>
        {currentStep === 'loading' && (
          <LoadingCard
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            transition={{ duration: 0.3 }}
          >
            <LoadingSpinner />
            <LoadingText>Analyzing your food...</LoadingText>
            <p style={{ color: 'rgba(255, 255, 255, 0.7)', marginTop: '10px' }}>
              Our AI is processing your request. This may take a few moments.
            </p>
          </LoadingCard>
        )}

        {currentStep === 'questions' && (
          <QuestionsCard
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h2 style={{ 
              color: 'white', 
              marginBottom: '30px', 
              fontFamily: 'Orbitron, monospace',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <AlertCircle size={24} />
              Clarification Questions
            </h2>
            
            {questions.map((question, index) => (
              <QuestionItem key={index}>
                <QuestionLabel>
                  <strong>Question {index + 1}:</strong> {question}
                </QuestionLabel>
                <QuestionInput
                  type="text"
                  placeholder="Your answer here..."
                  value={answers[index] || ''}
                  onChange={(e) => setAnswers(prev => ({ ...prev, [index]: e.target.value }))}
                />
              </QuestionItem>
            ))}

            <ButtonGroup>
              <ActionButton
                onClick={submitAnswers}
                disabled={isLoading}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                {isLoading ? <RefreshCw size={16} className="animate-spin" /> : <CheckCircle size={16} />}
                Submit Answers
              </ActionButton>
              
              <SecondaryButton
                onClick={skipQuestions}
                disabled={isLoading}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                Skip Questions
              </SecondaryButton>
            </ButtonGroup>
          </QuestionsCard>
        )}

        {currentStep === 'results' && results?.analysis_data && (
          <ResultsCard
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h2 style={{ 
              color: 'white', 
              marginBottom: '30px', 
              fontFamily: 'Orbitron, monospace',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <CheckCircle size={24} />
              Nutrition Results
            </h2>

            <ResultsGrid>
              {results.analysis_data.items?.map((item, index) => (
                <ResultItem
                  key={index}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <ItemTitle>{item.name}</ItemTitle>
                  <ItemQuantity><strong>Quantity:</strong> {item.quantity}</ItemQuantity>
                  
                  <ConfidenceBar>
                    <ConfidenceFill confidence={item.confidence || 0} />
                  </ConfidenceBar>
                  <p style={{ color: 'rgba(255, 255, 255, 0.6)', fontSize: '0.9rem', marginBottom: '15px' }}>
                    Confidence: {item.confidence || 0}%
                  </p>

                  <NutritionGrid>
                    <NutritionItem>
                      <NutritionLabel>Calories:</NutritionLabel>
                      <NutritionValue>{item.calories || 'N/A'}</NutritionValue>
                    </NutritionItem>
                    <NutritionItem>
                      <NutritionLabel>Protein:</NutritionLabel>
                      <NutritionValue>{item.protein || 'N/A'}g</NutritionValue>
                    </NutritionItem>
                    <NutritionItem>
                      <NutritionLabel>Carbs:</NutritionLabel>
                      <NutritionValue>{item.carbs || 'N/A'}g</NutritionValue>
                    </NutritionItem>
                    <NutritionItem>
                      <NutritionLabel>Fat:</NutritionLabel>
                      <NutritionValue>{item.fat || 'N/A'}g</NutritionValue>
                    </NutritionItem>
                  </NutritionGrid>
                </ResultItem>
              ))}

              {/* Total Summary */}
              <ResultItem
                gradient="linear-gradient(135deg, #667eea 0%, #764ba2 100%)"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: (results.analysis_data.items?.length || 0) * 0.1 }}
              >
                <ItemTitle style={{ color: '#90cdf4' }}>Total Nutrition</ItemTitle>
                <NutritionGrid>
                  <NutritionItem>
                    <NutritionLabel>Total Calories:</NutritionLabel>
                    <NutritionValue>{results.analysis_data.total_calories || 'N/A'}</NutritionValue>
                  </NutritionItem>
                  <NutritionItem>
                    <NutritionLabel>Total Protein:</NutritionLabel>
                    <NutritionValue>{results.analysis_data.total_protein || 'N/A'}g</NutritionValue>
                  </NutritionItem>
                  <NutritionItem>
                    <NutritionLabel>Total Carbs:</NutritionLabel>
                    <NutritionValue>{results.analysis_data.total_carbs || 'N/A'}g</NutritionValue>
                  </NutritionItem>
                  <NutritionItem>
                    <NutritionLabel>Total Fat:</NutritionLabel>
                    <NutritionValue>{results.analysis_data.total_fat || 'N/A'}g</NutritionValue>
                  </NutritionItem>
                </NutritionGrid>
              </ResultItem>
            </ResultsGrid>

            {/* Additional Features Section */}
            <div style={{ marginTop: '40px', borderTop: '1px solid rgba(255, 255, 255, 0.1)', paddingTop: '30px' }}>
              <h3 style={{ 
                color: 'white', 
                marginBottom: '20px', 
                fontFamily: 'Orbitron, monospace',
                display: 'flex',
                alignItems: 'center',
                gap: '12px'
              }}>
                <Lightbulb size={20} />
                Smart Features
              </h3>
              
              <ButtonGroup>
                <SecondaryButton
                  onClick={() => generateRecipe(results.analysis_data)}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <ChefHat size={16} />
                  Generate Recipe
                </SecondaryButton>
                
                <SecondaryButton
                  onClick={() => getHealthySwaps(results.analysis_data)}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <RefreshCw size={16} />
                  Healthy Swaps
                </SecondaryButton>
                
                <SecondaryButton
                  onClick={() => getNutritionInsights(results.analysis_data)}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Lightbulb size={16} />
                  Nutrition Insights
                </SecondaryButton>
                
                <SecondaryButton
                  onClick={() => openEditRecipe(results.analysis_data)}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Edit3 size={16} />
                  Edit Recipe
                </SecondaryButton>
              </ButtonGroup>
            </div>

            <ButtonGroup style={{ marginTop: '30px' }}>
              <ActionButton
                onClick={startNewAnalysis}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <RefreshCw size={16} />
                New Analysis
              </ActionButton>
              
              <SecondaryButton
                onClick={exportPDF}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
              >
                <Download size={16} />
                Export PDF
              </SecondaryButton>
            </ButtonGroup>
          </ResultsCard>
        )}
      </AnimatePresence>
      <AdvancedResultsModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        type={modalType}
        data={modalData}
        editedItems={editedItems}
        updateEditedItem={updateEditedItem}
        editClarifications={editClarifications}
        setEditClarifications={setEditClarifications}
        applyEditRecipe={applyEditRecipe}
      />
    </AnalysisContainer>
  );
};

export default FoodAnalysis;
