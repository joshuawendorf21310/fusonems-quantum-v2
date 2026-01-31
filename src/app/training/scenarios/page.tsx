'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Heart,
  AlertTriangle,
  Siren,
  Baby,
  Droplet,
  Play,
  RotateCcw,
  Clock,
  Trophy,
  TrendingUp,
  Users,
  ChevronRight,
  Star,
  Zap,
  Target,
  Award,
  Timer,
  Activity,
} from 'lucide-react';

interface Scenario {
  id: string;
  title: string;
  category: 'cardiac' | 'trauma' | 'medical' | 'ob' | 'peds' | 'stroke';
  difficulty: 'basic' | 'intermediate' | 'advanced' | 'paramedic';
  description: string;
  initialPresentation: string;
  timeLimit: number;
  icon: any;
  color: string;
}

interface Choice {
  id: string;
  text: string;
  outcome: 'critical' | 'good' | 'optimal';
  feedback: string;
  nextStep?: string;
}

interface DecisionPoint {
  id: string;
  prompt: string;
  vitals?: string;
  choices: Choice[];
  timeRemaining?: number;
}

const categories = [
  { value: 'cardiac', label: 'Cardiac', icon: Heart, color: 'from-red-500 to-pink-500' },
  { value: 'trauma', label: 'Trauma', icon: AlertTriangle, color: 'from-orange-500 to-red-500' },
  { value: 'medical', label: 'Medical', icon: Activity, color: 'from-blue-500 to-cyan-500' },
  { value: 'ob', label: 'OB/GYN', icon: Baby, color: 'from-pink-500 to-purple-500' },
  { value: 'peds', label: 'Pediatrics', icon: Baby, color: 'from-green-500 to-emerald-500' },
  { value: 'stroke', label: 'Stroke', icon: Droplet, color: 'from-purple-500 to-indigo-500' },
];

const scenarios: Scenario[] = [
  {
    id: '1',
    title: 'STEMI Alert',
    category: 'cardiac',
    difficulty: 'advanced',
    description: 'Crushing chest pain radiating to jaw',
    initialPresentation: '62 y/o male, severe substernal chest pain x 45 minutes',
    timeLimit: 300,
    icon: Heart,
    color: 'from-red-500 to-pink-500',
  },
  {
    id: '2',
    title: 'Multi-Trauma MVC',
    category: 'trauma',
    difficulty: 'paramedic',
    description: 'High-speed collision, entrapped driver',
    initialPresentation: 'Patient entrapped, obvious deformity to chest, difficulty breathing',
    timeLimit: 180,
    icon: AlertTriangle,
    color: 'from-orange-500 to-red-500',
  },
  {
    id: '3',
    title: 'Pediatric Respiratory Distress',
    category: 'peds',
    difficulty: 'intermediate',
    description: '3 y/o with wheezing and retractions',
    initialPresentation: 'Mom says started suddenly, child appears anxious, tripod position',
    timeLimit: 240,
    icon: Baby,
    color: 'from-green-500 to-emerald-500',
  },
  {
    id: '4',
    title: 'Altered Mental Status',
    category: 'medical',
    difficulty: 'basic',
    description: 'Found unresponsive by family',
    initialPresentation: '45 y/o found on couch, GCS 8, fruity breath odor',
    timeLimit: 300,
    icon: Activity,
    color: 'from-blue-500 to-cyan-500',
  },
  {
    id: '5',
    title: 'Active Labor Complications',
    category: 'ob',
    difficulty: 'advanced',
    description: 'Home birth, crowning with cord visible',
    initialPresentation: '28 y/o G3P2, contractions 2 min apart, urge to push',
    timeLimit: 180,
    icon: Baby,
    color: 'from-pink-500 to-purple-500',
  },
  {
    id: '6',
    title: 'Acute Stroke - Time Critical',
    category: 'stroke',
    difficulty: 'paramedic',
    description: 'Sudden onset left-sided weakness',
    initialPresentation: '71 y/o female, facial droop, slurred speech, last known normal 45 min ago',
    timeLimit: 120,
    icon: Droplet,
    color: 'from-purple-500 to-indigo-500',
  },
];

export default function ScenariosPage() {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [activeScenario, setActiveScenario] = useState<Scenario | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [timeRemaining, setTimeRemaining] = useState(0);
  const [score, setScore] = useState(0);
  const [choiceHistory, setChoiceHistory] = useState<any[]>([]);
  const [showResults, setShowResults] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

  useEffect(() => {
    if (activeScenario && timeRemaining > 0 && !isPaused && !showResults) {
      const timer = setInterval(() => {
        setTimeRemaining((prev) => Math.max(0, prev - 1));
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [activeScenario, timeRemaining, isPaused, showResults]);

  const startScenario = (scenario: Scenario) => {
    setActiveScenario(scenario);
    setCurrentStep(0);
    setTimeRemaining(scenario.timeLimit);
    setScore(0);
    setChoiceHistory([]);
    setShowResults(false);
    setIsPaused(false);
  };

  const makeChoice = (choice: Choice) => {
    const points = choice.outcome === 'optimal' ? 100 : choice.outcome === 'good' ? 50 : 0;
    setScore((prev) => prev + points);
    setChoiceHistory((prev) => [...prev, { step: currentStep, choice, points }]);

    if (currentStep >= 4 || choice.outcome === 'critical') {
      setShowResults(true);
    } else {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const resetScenario = () => {
    if (activeScenario) {
      startScenario(activeScenario);
    }
  };

  const getSampleDecisionPoint = (step: number): DecisionPoint => {
    const points: DecisionPoint[] = [
      {
        id: '1',
        prompt: 'Patient assessment reveals crushing chest pain. What is your immediate priority?',
        vitals: 'BP: 168/95 | HR: 118 irregular | RR: 24 | SpO2: 91% RA',
        choices: [
          {
            id: 'a',
            text: 'Apply high-flow O2, obtain 12-lead ECG',
            outcome: 'optimal',
            feedback: 'Excellent! Oxygen and rapid ECG acquisition are critical for STEMI recognition.',
            nextStep: 'Patient now on 15L NRB, SpO2 98%',
          },
          {
            id: 'b',
            text: 'Start IV, give aspirin',
            outcome: 'good',
            feedback: 'Good choice, but ECG should be done simultaneously for faster diagnosis.',
            nextStep: '18g IV established, aspirin given',
          },
          {
            id: 'c',
            text: 'Begin transport immediately',
            outcome: 'critical',
            feedback: 'Immediate transport without assessment delays critical interventions.',
            nextStep: 'Time lost',
          },
        ],
      },
      {
        id: '2',
        prompt: '12-lead shows ST elevation in leads II, III, aVF. What is your next action?',
        vitals: 'BP: 154/88 | HR: 108 | RR: 22 | SpO2: 98% on O2',
        choices: [
          {
            id: 'a',
            text: 'Call STEMI alert, notify cath lab, obtain IV access',
            outcome: 'optimal',
            feedback: 'Perfect! Early cath lab activation is proven to reduce mortality.',
            nextStep: 'Cath lab activated, ETA 8 minutes',
          },
          {
            id: 'b',
            text: 'Give nitro, morphine for pain',
            outcome: 'good',
            feedback: 'Pain management is important but STEMI alert should be first priority.',
            nextStep: 'Pain reduced but cath lab notification delayed',
          },
          {
            id: 'c',
            text: 'Transport to closest hospital',
            outcome: 'critical',
            feedback: 'STEMI requires PCI-capable facility. Wrong destination = poor outcome.',
            nextStep: 'Wrong destination chosen',
          },
        ],
      },
      {
        id: '3',
        prompt: 'En route, patient becomes hypotensive (BP 88/52). What do you do?',
        vitals: 'BP: 88/52 | HR: 116 | RR: 26 | SpO2: 97% on O2',
        choices: [
          {
            id: 'a',
            text: 'Hold nitro, give fluid bolus, reassess',
            outcome: 'optimal',
            feedback: 'Excellent! Inferior STEMI can involve RV - avoid nitro when hypotensive.',
            nextStep: 'BP improved to 102/64 after 250mL bolus',
          },
          {
            id: 'b',
            text: 'Continue nitro as ordered',
            outcome: 'critical',
            feedback: 'Nitro in hypotensive patient can cause cardiovascular collapse.',
            nextStep: 'BP drops to 70/40',
          },
          {
            id: 'c',
            text: 'Start dopamine drip',
            outcome: 'good',
            feedback: 'May help but fluid challenge should be tried first in RV infarct.',
            nextStep: 'BP stabilizes but more complex than needed',
          },
        ],
      },
      {
        id: '4',
        prompt: 'Patient arrives at cath lab stable. What post-call documentation is critical?',
        vitals: 'BP: 118/72 | HR: 94 | RR: 18 | SpO2: 99% on O2',
        choices: [
          {
            id: 'a',
            text: 'Exact times: symptom onset, 12-lead, STEMI alert, door time',
            outcome: 'optimal',
            feedback: 'Perfect! Time documentation is essential for quality metrics and patient care.',
            nextStep: 'Complete documentation submitted',
          },
          {
            id: 'b',
            text: 'Standard PCR with treatments given',
            outcome: 'good',
            feedback: 'Good but missing critical timing data needed for quality review.',
            nextStep: 'Documentation adequate but incomplete',
          },
          {
            id: 'c',
            text: 'Brief narrative only',
            outcome: 'critical',
            feedback: 'Insufficient documentation can affect reimbursement and QI.',
            nextStep: 'Poor documentation',
          },
        ],
      },
      {
        id: '5',
        prompt: 'Patient outcome: Door-to-balloon time 47 minutes. How do you feel about your performance?',
        vitals: 'Patient stable post-PCI, prognosis excellent',
        choices: [
          {
            id: 'a',
            text: 'Review what went well and identify areas for improvement',
            outcome: 'optimal',
            feedback: 'Excellent reflective practice! Continuous improvement saves lives.',
            nextStep: 'Scenario complete',
          },
          {
            id: 'b',
            text: 'Feel satisfied with outcome',
            outcome: 'good',
            feedback: 'Good outcome, but always look for ways to improve response times.',
            nextStep: 'Scenario complete',
          },
          {
            id: 'c',
            text: 'Move on to next call',
            outcome: 'critical',
            feedback: 'Missing learning opportunity. Reflection is key to professional growth.',
            nextStep: 'Scenario complete',
          },
        ],
      },
    ];
    return points[step] || points[0];
  };

  const filteredScenarios = selectedCategory
    ? scenarios.filter((s) => s.category === selectedCategory)
    : scenarios;

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 p-6">
      {!activeScenario ? (
        <>
          {/* Header */}
          <motion.div
            initial={{ y: -20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            className="max-w-7xl mx-auto mb-8"
          >
            <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-8">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <motion.div
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="w-20 h-20 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-2xl flex items-center justify-center"
                  >
                    <Play className="w-10 h-10 text-white" />
                  </motion.div>
                  <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
                      Interactive Scenarios
                    </h1>
                    <p className="text-gray-600 text-lg">
                      Real-world simulations with branching decisions
                    </p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <div className="bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl p-6 text-white">
                    <div className="flex items-center gap-2 mb-2">
                      <Trophy className="w-6 h-6" />
                      <span className="text-sm font-medium">Total Score</span>
                    </div>
                    <div className="text-3xl font-bold">8,947</div>
                  </div>
                  <div className="bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl p-6 text-white">
                    <div className="flex items-center gap-2 mb-2">
                      <Target className="w-6 h-6" />
                      <span className="text-sm font-medium">Completed</span>
                    </div>
                    <div className="text-3xl font-bold">23</div>
                  </div>
                </div>
              </div>

              {/* Category Filter */}
              <div className="mt-8 flex gap-3 overflow-x-auto pb-2">
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() => setSelectedCategory(null)}
                  className={`px-6 py-3 rounded-xl font-medium whitespace-nowrap transition-all ${
                    selectedCategory === null
                      ? 'bg-gradient-to-r from-indigo-500 to-purple-500 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  All Scenarios
                </motion.button>
                {categories.map((cat) => (
                  <motion.button
                    key={cat.value}
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setSelectedCategory(cat.value)}
                    className={`px-6 py-3 rounded-xl font-medium whitespace-nowrap transition-all ${
                      selectedCategory === cat.value
                        ? `bg-gradient-to-r ${cat.color} text-white shadow-lg`
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <cat.icon className="w-4 h-4" />
                      {cat.label}
                    </div>
                  </motion.button>
                ))}
              </div>
            </div>
          </motion.div>

          {/* Scenarios Grid */}
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredScenarios.map((scenario, idx) => {
                const CategoryIcon = scenario.icon;
                return (
                  <motion.div
                    key={scenario.id}
                    initial={{ y: 20, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    transition={{ delay: idx * 0.1 }}
                    whileHover={{ y: -5, scale: 1.02 }}
                    className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-xl border border-white/20 overflow-hidden cursor-pointer group"
                    onClick={() => startScenario(scenario)}
                  >
                    <div className={`h-32 bg-gradient-to-br ${scenario.color} p-6 relative overflow-hidden`}>
                      <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
                        className="absolute top-0 right-0 w-32 h-32 opacity-20"
                      >
                        <CategoryIcon className="w-full h-full text-white" />
                      </motion.div>
                      <div className="relative z-10">
                        <div className="flex items-center gap-2 mb-2">
                          <CategoryIcon className="w-6 h-6 text-white" />
                          <span className="text-white/80 text-sm font-medium uppercase tracking-wide">
                            {scenario.category}
                          </span>
                        </div>
                        <h3 className="text-2xl font-bold text-white">{scenario.title}</h3>
                      </div>
                    </div>

                    <div className="p-6">
                      <p className="text-gray-700 mb-4">{scenario.description}</p>
                      <div className="flex items-center justify-between mb-4">
                        <span
                          className={`px-3 py-1 rounded-lg text-xs font-bold uppercase ${
                            scenario.difficulty === 'basic'
                              ? 'bg-green-100 text-green-700'
                              : scenario.difficulty === 'intermediate'
                              ? 'bg-blue-100 text-blue-700'
                              : scenario.difficulty === 'advanced'
                              ? 'bg-orange-100 text-orange-700'
                              : 'bg-red-100 text-red-700'
                          }`}
                        >
                          {scenario.difficulty}
                        </span>
                        <div className="flex items-center gap-1 text-gray-600">
                          <Clock className="w-4 h-4" />
                          <span className="text-sm">{formatTime(scenario.timeLimit)}</span>
                        </div>
                      </div>

                      <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        className={`w-full py-3 bg-gradient-to-r ${scenario.color} text-white rounded-xl font-medium shadow-lg flex items-center justify-center gap-2 group-hover:shadow-2xl transition-all`}
                      >
                        <Play className="w-5 h-5" />
                        Start Scenario
                      </motion.button>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </>
      ) : (
        <AnimatePresence mode="wait">
          {!showResults ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="max-w-5xl mx-auto"
            >
              {/* Scenario Header */}
              <motion.div
                initial={{ y: -20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-6 mb-6"
              >
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-4">
                    <div className={`w-16 h-16 bg-gradient-to-br ${activeScenario.color} rounded-2xl flex items-center justify-center`}>
                      <activeScenario.icon className="w-8 h-8 text-white" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-bold text-gray-800">{activeScenario.title}</h2>
                      <p className="text-gray-600">Step {currentStep + 1} of 5</p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    {/* Timer */}
                    <div className="bg-gradient-to-br from-red-500 to-orange-500 rounded-2xl p-4 text-white">
                      <div className="flex items-center gap-2 mb-1">
                        <Timer className="w-5 h-5" />
                        <span className="text-sm font-medium">Time Remaining</span>
                      </div>
                      <div className="text-3xl font-bold tabular-nums">{formatTime(timeRemaining)}</div>
                    </div>

                    {/* Score */}
                    <div className="bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl p-4 text-white">
                      <div className="flex items-center gap-2 mb-1">
                        <Star className="w-5 h-5" />
                        <span className="text-sm font-medium">Score</span>
                      </div>
                      <div className="text-3xl font-bold">{score}</div>
                    </div>
                  </div>
                </div>

                {/* Progress Bar */}
                <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${((currentStep + 1) / 5) * 100}%` }}
                    className={`h-full bg-gradient-to-r ${activeScenario.color}`}
                  />
                </div>
              </motion.div>

              {/* Decision Point */}
              <motion.div
                key={currentStep}
                initial={{ x: 100, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -100, opacity: 0 }}
                className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-8"
              >
                <div className="mb-8">
                  <h3 className="text-2xl font-bold text-gray-800 mb-4">
                    {getSampleDecisionPoint(currentStep).prompt}
                  </h3>
                  {getSampleDecisionPoint(currentStep).vitals && (
                    <div className="bg-gradient-to-r from-red-50 to-orange-50 rounded-2xl p-4 border-l-4 border-red-500">
                      <div className="flex items-center gap-2 mb-2">
                        <Activity className="w-5 h-5 text-red-600" />
                        <span className="font-bold text-red-600">Vital Signs</span>
                      </div>
                      <p className="text-gray-700 font-mono">
                        {getSampleDecisionPoint(currentStep).vitals}
                      </p>
                    </div>
                  )}
                </div>

                {/* Choices */}
                <div className="space-y-4">
                  {getSampleDecisionPoint(currentStep).choices.map((choice, idx) => (
                    <motion.button
                      key={choice.id}
                      initial={{ x: 50, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: idx * 0.1 }}
                      whileHover={{ scale: 1.02, x: 10 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => makeChoice(choice)}
                      className="w-full p-6 bg-gradient-to-r from-gray-50 to-gray-100 hover:from-indigo-50 hover:to-purple-50 rounded-2xl text-left transition-all group border-2 border-transparent hover:border-indigo-300"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl flex items-center justify-center text-white font-bold text-xl group-hover:scale-110 transition-transform">
                            {String.fromCharCode(65 + idx)}
                          </div>
                          <p className="text-gray-800 font-medium text-lg">{choice.text}</p>
                        </div>
                        <ChevronRight className="w-6 h-6 text-gray-400 group-hover:text-indigo-600 group-hover:translate-x-2 transition-all" />
                      </div>
                    </motion.button>
                  ))}
                </div>
              </motion.div>

              {/* Exit Button */}
              <motion.button
                initial={{ y: 20, opacity: 0 }}
                animate={{ y: 0, opacity: 1 }}
                onClick={() => setActiveScenario(null)}
                className="mt-6 px-6 py-3 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-xl font-medium transition-all"
              >
                Exit Scenario
              </motion.button>
            </motion.div>
          ) : (
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="max-w-4xl mx-auto"
            >
              {/* Results */}
              <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-8">
                <div className="text-center mb-8">
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    transition={{ type: 'spring', duration: 0.6 }}
                    className="w-32 h-32 bg-gradient-to-br from-yellow-400 to-orange-400 rounded-full flex items-center justify-center mx-auto mb-6"
                  >
                    <Trophy className="w-16 h-16 text-white" />
                  </motion.div>
                  <h2 className="text-4xl font-bold text-gray-800 mb-2">Scenario Complete!</h2>
                  <p className="text-gray-600 text-lg">Here's how you performed</p>
                </div>

                {/* Score Breakdown */}
                <div className="grid grid-cols-3 gap-4 mb-8">
                  <div className="bg-gradient-to-br from-purple-500 to-indigo-500 rounded-2xl p-6 text-white text-center">
                    <div className="text-4xl font-bold mb-2">{score}</div>
                    <div className="text-sm">Total Score</div>
                  </div>
                  <div className="bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl p-6 text-white text-center">
                    <div className="text-4xl font-bold mb-2">
                      {choiceHistory.filter((c) => c.choice.outcome === 'optimal').length}
                    </div>
                    <div className="text-sm">Optimal Choices</div>
                  </div>
                  <div className="bg-gradient-to-br from-blue-500 to-cyan-500 rounded-2xl p-6 text-white text-center">
                    <div className="text-4xl font-bold mb-2">{formatTime(activeScenario.timeLimit - timeRemaining)}</div>
                    <div className="text-sm">Time Taken</div>
                  </div>
                </div>

                {/* Choice Review */}
                <div className="space-y-4 mb-8">
                  <h3 className="text-xl font-bold text-gray-800">Decision Review</h3>
                  {choiceHistory.map((item, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ x: -20, opacity: 0 }}
                      animate={{ x: 0, opacity: 1 }}
                      transition={{ delay: idx * 0.1 }}
                      className={`p-4 rounded-2xl border-l-4 ${
                        item.choice.outcome === 'optimal'
                          ? 'bg-green-50 border-green-500'
                          : item.choice.outcome === 'good'
                          ? 'bg-blue-50 border-blue-500'
                          : 'bg-red-50 border-red-500'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <span className="font-bold text-gray-800">Step {item.step + 1}:</span>
                          <span className="text-gray-700 ml-2">{item.choice.text}</span>
                        </div>
                        <span
                          className={`px-3 py-1 rounded-lg text-xs font-bold ${
                            item.choice.outcome === 'optimal'
                              ? 'bg-green-200 text-green-800'
                              : item.choice.outcome === 'good'
                              ? 'bg-blue-200 text-blue-800'
                              : 'bg-red-200 text-red-800'
                          }`}
                        >
                          +{item.points}
                        </span>
                      </div>
                      <p className="text-gray-600 text-sm">{item.choice.feedback}</p>
                    </motion.div>
                  ))}
                </div>

                {/* Peer Comparison */}
                <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-2xl p-6 mb-8">
                  <div className="flex items-center gap-2 mb-4">
                    <Users className="w-6 h-6 text-indigo-600" />
                    <h3 className="text-lg font-bold text-gray-800">Peer Comparison</h3>
                  </div>
                  <div className="space-y-3">
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm text-gray-600">Your Score</span>
                        <span className="text-sm font-bold text-gray-800">{score} / 500</span>
                      </div>
                      <div className="h-3 bg-white/50 rounded-full overflow-hidden">
                        <motion.div
                          initial={{ width: 0 }}
                          animate={{ width: `${(score / 500) * 100}%` }}
                          className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
                        />
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between mb-1">
                        <span className="text-sm text-gray-600">Average Score</span>
                        <span className="text-sm font-bold text-gray-800">312 / 500</span>
                      </div>
                      <div className="h-3 bg-white/50 rounded-full overflow-hidden">
                        <div className="h-full w-[62%] bg-gray-400" />
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 text-center">
                    <span className="text-2xl font-bold text-indigo-600">
                      Top {Math.round((1 - score / 500) * 100)}%
                    </span>
                    <p className="text-gray-600 text-sm mt-1">You performed better than most users!</p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex gap-4">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={resetScenario}
                    className="flex-1 py-4 bg-gradient-to-r from-indigo-500 to-purple-500 text-white rounded-xl font-bold text-lg shadow-lg flex items-center justify-center gap-2"
                  >
                    <RotateCcw className="w-6 h-6" />
                    Try Again
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setActiveScenario(null)}
                    className="flex-1 py-4 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl font-bold text-lg shadow-lg flex items-center justify-center gap-2"
                  >
                    <ChevronRight className="w-6 h-6" />
                    Next Scenario
                  </motion.button>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </div>
  );
}
