# FITKIT - Modern React Frontend

A modern, futuristic React frontend for the FITKIT Smart Food Analyzer application. This project transforms the original HTML application into a sleek, responsive React application with advanced UI/UX features.

## 🚀 Features

### Core Functionality
- **AI-Powered Food Analysis**: Upload images or describe food for instant nutrition analysis
- **Google Authentication**: Secure login with Google OAuth
- **Personalized Dashboard**: Customizable user profiles and health insights
- **Meal History Tracking**: Comprehensive meal logging and analytics
- **Meal Plan Generator**: AI-generated personalized meal plans
- **AI Health Coach**: Interactive chatbot overlay for nutrition guidance

### Modern UI/UX
- **Futuristic Design**: Dark theme with neon accents and glass morphism effects
- **Smooth Animations**: Framer Motion powered transitions and micro-interactions
- **Responsive Layout**: Mobile-first design that works on all devices
- **Interactive Elements**: Hover effects, loading states, and visual feedback
- **Accessibility**: WCAG compliant with proper contrast and keyboard navigation

### Technical Features
- **React 18**: Latest React with hooks and modern patterns
- **Styled Components**: CSS-in-JS with dynamic theming
- **React Router**: Client-side routing with protected routes
- **Context API**: Global state management
- **Error Handling**: Comprehensive error boundaries and user feedback
- **Offline Support**: Graceful degradation when offline

## 🛠️ Technology Stack

- **Frontend Framework**: React 18.2.0
- **Styling**: Styled Components 5.3.5
- **Animations**: Framer Motion 7.2.1
- **Routing**: React Router DOM 6.3.0
- **Icons**: Lucide React 0.263.1
- **PDF Generation**: jsPDF 2.5.1
- **Build Tool**: Create React App 5.0.1

## 📁 Project Structure

```
src/
├── components/
│   ├── Auth/
│   │   └── Login.js                 # Google OAuth login
│   ├── Common/
│   │   ├── Toast.js                 # Notification system
│   │   └── ConnectionStatus.js      # Network status indicator
│   ├── Navigation/
│   │   └── Navigation.js            # Main navigation bar
│   ├── Dashboard/
│   │   └── Dashboard.js             # User dashboard with insights
│   ├── Analysis/
│   │   └── FoodAnalysis.js          # Food analysis interface
│   ├── History/
│   │   └── MealHistory.js           # Meal history and analytics
│   ├── MealPlan/
│   │   └── MealPlan.js              # Meal plan generator
│   └── AIHealthCoach/
│       └── AIHealthCoach.js         # AI chatbot overlay
├── App.js                           # Main app component
├── index.js                         # App entry point
└── index.css                        # Global styles and theme
```

## 🎨 Design System

### Color Palette
- **Primary**: Linear gradients with blues (#667eea) and purples (#764ba2)
- **Secondary**: Green (#48bb78) for success states
- **Accent**: Orange (#ed8936) for highlights
- **Background**: Dark gradient (#0f0f23 to #16213e)
- **Text**: White with various opacity levels

### Typography
- **Primary Font**: Inter (body text)
- **Display Font**: Orbitron (headings and UI elements)
- **Font Weights**: 300-900 range for hierarchy

### Components
- **Glass Morphism**: Translucent cards with backdrop blur
- **Neon Effects**: Glowing borders and text shadows
- **Smooth Transitions**: 0.3s ease transitions throughout
- **Hover States**: Subtle lift and glow effects

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+ 
- npm or yarn
- Modern web browser

### Installation

This project consists of a Python FastAPI backend and a React frontend. Follow these steps in order:

#### Step 1: Setup Backend (FastAPI)

1. **Navigate to the backend directory**
   ```bash
   cd FITKIT-main
   ```

2. **Create and activate virtual environment**
   ```bash
   # Create virtual environment
   python -m venv myvenv
   
   # Activate virtual environment
   # On Windows:
   myvenv\Scripts\activate
   # On macOS/Linux:
   source myvenv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python app/init_db.py
   ```

5. **Start the backend server**
   ```bash
   uvicorn app.main:app --reload
   ```
   
   The backend API will be available at `http://localhost:8000`

#### Step 2: Setup Frontend (React)

6. **Open a new terminal and navigate back to the root directory**
   ```bash
   cd ..
   ```

7. **Install frontend dependencies**
   ```bash
   npm install
   ```

8. **Start the frontend development server**
   ```bash
   npm start
   ```

9. **Open your browser**
   Navigate to `http://localhost:3000`

### Environment Setup

The React frontend expects the FastAPI backend to be running on:
- Development: `http://localhost:8000`
- Production: Configure `BASE_URL` in `src/App.js`

Make sure both servers are running simultaneously for the application to work properly.

## 🔧 Configuration

### Google OAuth Setup
Update the Google Client ID in `src/App.js`:
```javascript
const GOOGLE_CLIENT_ID = "your-google-client-id";
```

### API Endpoints
The application connects to these backend endpoints:
- `/health` - Health check
- `/sessions/` - Session management
- `/users/google` - Google authentication
- `/users/{id}` - User profile management
- `/analysis/*` - Food analysis endpoints
- `/agent/*` - AI health coach endpoints
- `/recommendations/*` - Meal plans and recommendations

## 📱 Key Components

### AI Health Coach Overlay
- **Location**: Bottom-right corner floating button
- **Features**: 
  - Expandable chat interface
  - Quick action buttons
  - Typing indicators
  - Message history
  - Minimize/maximize functionality

### Dashboard
- **Quick Actions**: Direct access to main features
- **Personalization**: User profile settings
- **Health Insights**: Statistics and recommendations
- **Responsive Grid**: Adapts to screen size

### Food Analysis
- **Dual Input**: Image upload or text description
- **Real-time Preview**: Image preview before analysis
- **Step-by-step Flow**: Loading → Questions → Results
- **Rich Results**: Detailed nutrition breakdown

### Meal History
- **Advanced Filtering**: Search, date range, sorting
- **Statistics Dashboard**: Aggregated nutrition data
- **Expandable Cards**: Detailed meal information
- **Export Functionality**: PDF generation (planned)

## 🎯 User Experience

### Navigation Flow
1. **Login**: Google OAuth authentication
2. **Dashboard**: Overview and quick actions
3. **Analysis**: Food analysis workflow
4. **History**: Past meal tracking
5. **Meal Plan**: Personalized planning
6. **AI Coach**: Always accessible help

### Responsive Design
- **Mobile**: Collapsible navigation, stacked layouts
- **Tablet**: Optimized grid layouts
- **Desktop**: Full feature set with hover states

### Loading States
- **Skeleton Loading**: Smooth content loading
- **Progress Indicators**: Clear feedback during operations
- **Error Handling**: User-friendly error messages

## 🔮 Future Enhancements

### Planned Features
- **Dark/Light Theme Toggle**: User preference system
- **Advanced Analytics**: Charts and trend analysis
- **Social Features**: Meal sharing and community
- **Offline Mode**: PWA capabilities
- **Voice Input**: Speech-to-text for food logging
- **Barcode Scanner**: Product identification
- **Wearable Integration**: Fitness tracker sync

### Technical Improvements
- **Performance**: Code splitting and lazy loading
- **Testing**: Comprehensive test suite
- **Accessibility**: Enhanced screen reader support
- **Internationalization**: Multi-language support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Original HTML Version**: Foundation for the React conversion
- **Design Inspiration**: Modern fitness and health applications
- **Icons**: Lucide React icon library
- **Fonts**: Google Fonts (Inter & Orbitron)

---

**Built with ❤️ for a healthier future**
