'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Brain,
  Layers,
  Clock,
  TrendingUp,
  Zap,
  Star,
  Plus,
  RotateCcw,
  Play,
  Pause,
  Check,
  X,
  AlertCircle,
  Award,
  Calendar,
  Target,
  Download,
  Upload,
} from 'lucide-react';

interface Flashcard {
  id: string;
  front: string;
  back: string;
  category: string;
  difficulty: number;
  interval: number;
  repetitions: number;
  easeFactor: number;
  nextReview: Date;
  lastReviewed?: Date;
}

interface StudySession {
  cardsReviewed: number;
  duration: number;
  correctCount: number;
  startTime: Date;
}

export default function SpacedReviewPage() {
  const [decks, setDecks] = useState([
    { id: '1', name: 'ACLS Protocols', cards: 45, dueCards: 12, color: 'from-red-500 to-pink-500' },
    { id: '2', name: 'Drug Dosages', cards: 89, dueCards: 23, color: 'from-blue-500 to-cyan-500' },
    { id: '3', name: 'Anatomy & Physiology', cards: 156, dueCards: 34, color: 'from-green-500 to-emerald-500' },
    { id: '4', name: 'Medical Terminology', cards: 203, dueCards: 8, color: 'from-purple-500 to-indigo-500' },
    { id: '5', name: 'Trauma Assessment', cards: 67, dueCards: 15, color: 'from-orange-500 to-red-500' },
    { id: '6', name: 'Pediatric Care', cards: 92, dueCards: 19, color: 'from-pink-500 to-purple-500' },
  ]);

  const [activeDeck, setActiveDeck] = useState<string | null>(null);
  const [currentCard, setCurrentCard] = useState<Flashcard | null>(null);
  const [isFlipped, setIsFlipped] = useState(false);
  const [studySession, setStudySession] = useState<StudySession | null>(null);
  const [sessionTimer, setSessionTimer] = useState(0);
  const [streak, setStreak] = useState(7);
  const [showStats, setShowStats] = useState(false);

  // Sample flashcards for demo
  const sampleCards: Flashcard[] = [
    {
      id: '1',
      front: 'What is the initial dose of epinephrine in cardiac arrest?',
      back: '1 mg (1:10,000) IV/IO every 3-5 minutes',
      category: 'ACLS',
      difficulty: 2,
      interval: 1,
      repetitions: 0,
      easeFactor: 2.5,
      nextReview: new Date(),
    },
    {
      id: '2',
      front: 'What are the 5 H\'s of reversible causes of cardiac arrest?',
      back: 'Hypovolemia, Hypoxia, Hydrogen ion (acidosis), Hypo/Hyperkalemia, Hypothermia',
      category: 'ACLS',
      difficulty: 3,
      interval: 1,
      repetitions: 0,
      easeFactor: 2.5,
      nextReview: new Date(),
    },
    {
      id: '3',
      front: 'What is the maximum dose of adenosine?',
      back: 'First dose: 6mg rapid IV push. Second dose: 12mg (can repeat once)',
      category: 'Drugs',
      difficulty: 2,
      interval: 1,
      repetitions: 0,
      easeFactor: 2.5,
      nextReview: new Date(),
    },
  ];

  const [studyCards, setStudyCards] = useState<Flashcard[]>(sampleCards);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (studySession) {
      const timer = setInterval(() => {
        setSessionTimer((prev) => prev + 1);
      }, 1000);
      return () => clearInterval(timer);
    }
  }, [studySession]);

  const startStudySession = (deckId: string) => {
    setActiveDeck(deckId);
    setStudySession({
      cardsReviewed: 0,
      duration: 0,
      correctCount: 0,
      startTime: new Date(),
    });
    setSessionTimer(0);
    setCurrentIndex(0);
    setCurrentCard(studyCards[0]);
    setIsFlipped(false);
  };

  const rateCard = (quality: 'again' | 'hard' | 'good' | 'easy') => {
    if (!currentCard || !studySession) return;

    // SM-2 Algorithm
    let newInterval = currentCard.interval;
    let newRepetitions = currentCard.repetitions;
    let newEaseFactor = currentCard.easeFactor;

    const qualityMap = { again: 0, hard: 3, good: 4, easy: 5 };
    const q = qualityMap[quality];

    if (q >= 3) {
      if (newRepetitions === 0) {
        newInterval = 1;
      } else if (newRepetitions === 1) {
        newInterval = 6;
      } else {
        newInterval = Math.round(newInterval * newEaseFactor);
      }
      newRepetitions += 1;
    } else {
      newRepetitions = 0;
      newInterval = 1;
    }

    newEaseFactor = newEaseFactor + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02));
    if (newEaseFactor < 1.3) newEaseFactor = 1.3;

    const nextReview = new Date();
    nextReview.setDate(nextReview.getDate() + newInterval);

    setStudyCards((prev) =>
      prev.map((card) =>
        card.id === currentCard.id
          ? {
              ...card,
              interval: newInterval,
              repetitions: newRepetitions,
              easeFactor: newEaseFactor,
              nextReview,
              lastReviewed: new Date(),
            }
          : card
      )
    );

    setStudySession({
      ...studySession,
      cardsReviewed: studySession.cardsReviewed + 1,
      correctCount: studySession.correctCount + (q >= 3 ? 1 : 0),
    });

    // Move to next card
    if (currentIndex < studyCards.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setCurrentCard(studyCards[currentIndex + 1]);
      setIsFlipped(false);
    } else {
      setActiveDeck(null);
      setStudySession(null);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-purple-50 to-pink-50 p-6">
      {!activeDeck ? (
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
                    animate={{ rotateY: [0, 180, 360] }}
                    transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
                    className="w-20 h-20 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-2xl flex items-center justify-center"
                  >
                    <Brain className="w-10 h-10 text-white" />
                  </motion.div>
                  <div>
                    <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-indigo-600 bg-clip-text text-transparent">
                      Spaced Repetition
                    </h1>
                    <p className="text-gray-600 text-lg">
                      Science-based flashcards for long-term retention
                    </p>
                  </div>
                </div>

                <div className="flex gap-4">
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setShowStats(!showStats)}
                    className="px-6 py-3 bg-gradient-to-r from-blue-500 to-cyan-500 text-white rounded-xl font-medium shadow-lg flex items-center gap-2"
                  >
                    <TrendingUp className="w-5 h-5" />
                    Statistics
                  </motion.button>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    className="px-6 py-3 bg-gradient-to-r from-green-500 to-emerald-500 text-white rounded-xl font-medium shadow-lg flex items-center gap-2"
                  >
                    <Plus className="w-5 h-5" />
                    New Deck
                  </motion.button>
                </div>
              </div>
            </div>
          </motion.div>

          {/* Stats Dashboard */}
          <div className="max-w-7xl mx-auto mb-8 grid grid-cols-1 md:grid-cols-4 gap-6">
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="bg-gradient-to-br from-orange-500 to-red-500 rounded-3xl p-6 text-white shadow-xl"
            >
              <div className="flex items-center gap-3 mb-3">
                <Zap className="w-8 h-8" />
                <span className="text-sm font-medium uppercase tracking-wide">Due Today</span>
              </div>
              <div className="text-5xl font-bold mb-2">111</div>
              <div className="text-sm opacity-80">cards to review</div>
            </motion.div>

            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.1 }}
              className="bg-gradient-to-br from-purple-500 to-indigo-500 rounded-3xl p-6 text-white shadow-xl"
            >
              <div className="flex items-center gap-3 mb-3">
                <Target className="w-8 h-8" />
                <span className="text-sm font-medium uppercase tracking-wide">Retention</span>
              </div>
              <div className="text-5xl font-bold mb-2">89%</div>
              <div className="text-sm opacity-80">overall accuracy</div>
            </motion.div>

            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.2 }}
              className="bg-gradient-to-br from-green-500 to-emerald-500 rounded-3xl p-6 text-white shadow-xl"
            >
              <div className="flex items-center gap-3 mb-3">
                <Award className="w-8 h-8" />
                <span className="text-sm font-medium uppercase tracking-wide">Streak</span>
              </div>
              <div className="text-5xl font-bold mb-2">{streak}</div>
              <div className="text-sm opacity-80">days in a row</div>
            </motion.div>

            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: 0.3 }}
              className="bg-gradient-to-br from-blue-500 to-cyan-500 rounded-3xl p-6 text-white shadow-xl"
            >
              <div className="flex items-center gap-3 mb-3">
                <Layers className="w-8 h-8" />
                <span className="text-sm font-medium uppercase tracking-wide">Total Cards</span>
              </div>
              <div className="text-5xl font-bold mb-2">652</div>
              <div className="text-sm opacity-80">across all decks</div>
            </motion.div>
          </div>

          {/* Decks Grid */}
          <div className="max-w-7xl mx-auto">
            <h2 className="text-2xl font-bold text-gray-800 mb-6">Your Decks</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {decks.map((deck, idx) => (
                <motion.div
                  key={deck.id}
                  initial={{ y: 20, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  transition={{ delay: idx * 0.1 }}
                  whileHover={{ y: -5, scale: 1.02 }}
                  className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-xl border border-white/20 overflow-hidden group cursor-pointer"
                >
                  <div className={`h-32 bg-gradient-to-br ${deck.color} p-6 relative overflow-hidden`}>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 20, repeat: Infinity, ease: 'linear' }}
                      className="absolute top-0 right-0 w-32 h-32 opacity-20"
                    >
                      <Layers className="w-full h-full text-white" />
                    </motion.div>
                    <div className="relative z-10">
                      <h3 className="text-2xl font-bold text-white mb-2">{deck.name}</h3>
                      <div className="flex items-center gap-2 text-white/80 text-sm">
                        <Clock className="w-4 h-4" />
                        <span>{deck.dueCards} due</span>
                      </div>
                    </div>
                  </div>

                  <div className="p-6">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <div className="text-3xl font-bold text-gray-800">{deck.cards}</div>
                        <div className="text-sm text-gray-600">total cards</div>
                      </div>
                      {deck.dueCards > 0 && (
                        <div className="px-4 py-2 bg-red-100 text-red-600 rounded-xl font-bold">
                          {deck.dueCards} due
                        </div>
                      )}
                    </div>

                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => startStudySession(deck.id)}
                      disabled={deck.dueCards === 0}
                      className={`w-full py-3 rounded-xl font-medium shadow-lg flex items-center justify-center gap-2 transition-all ${
                        deck.dueCards > 0
                          ? `bg-gradient-to-r ${deck.color} text-white group-hover:shadow-2xl`
                          : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                      }`}
                    >
                      <Play className="w-5 h-5" />
                      {deck.dueCards > 0 ? 'Study Now' : 'All Caught Up!'}
                    </motion.button>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Retention Graph */}
          {showStats && (
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              className="max-w-7xl mx-auto mt-8"
            >
              <div className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-8">
                <h3 className="text-2xl font-bold text-gray-800 mb-6">Knowledge Retention</h3>
                <div className="h-64 flex items-end gap-4">
                  {[92, 89, 91, 87, 89, 90, 89].map((value, idx) => (
                    <div key={idx} className="flex-1 flex flex-col items-center">
                      <motion.div
                        initial={{ height: 0 }}
                        animate={{ height: `${value}%` }}
                        transition={{ delay: idx * 0.1, duration: 0.5 }}
                        className="w-full bg-gradient-to-t from-purple-500 to-indigo-500 rounded-t-xl relative group"
                      >
                        <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-800 text-white px-2 py-1 rounded text-sm opacity-0 group-hover:opacity-100 transition-opacity">
                          {value}%
                        </div>
                      </motion.div>
                      <div className="mt-2 text-xs text-gray-600 font-medium">
                        {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][idx]}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </>
      ) : (
        <AnimatePresence mode="wait">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="max-w-4xl mx-auto"
          >
            {/* Session Header */}
            <motion.div
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              className="bg-white/80 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-6 mb-6"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="text-gray-600">
                    Card {currentIndex + 1} of {studyCards.length}
                  </div>
                  <div className="h-2 w-64 bg-gray-200 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${((currentIndex + 1) / studyCards.length) * 100}%` }}
                      className="h-full bg-gradient-to-r from-purple-500 to-indigo-500"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-6">
                  <div className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-gray-600" />
                    <span className="text-xl font-bold text-gray-800">{formatTime(sessionTimer)}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Check className="w-5 h-5 text-green-600" />
                    <span className="text-xl font-bold text-gray-800">{studySession?.correctCount || 0}</span>
                  </div>
                  <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => setActiveDeck(null)}
                    className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-800 rounded-xl font-medium"
                  >
                    Exit
                  </motion.button>
                </div>
              </div>
            </motion.div>

            {/* Flashcard */}
            {currentCard && (
              <motion.div
                key={currentCard.id}
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="relative h-96 cursor-pointer"
                onClick={() => setIsFlipped(!isFlipped)}
              >
                <AnimatePresence mode="wait">
                  {!isFlipped ? (
                    <motion.div
                      key="front"
                      initial={{ rotateY: 90 }}
                      animate={{ rotateY: 0 }}
                      exit={{ rotateY: -90 }}
                      transition={{ duration: 0.3 }}
                      className="absolute inset-0 bg-white/90 backdrop-blur-xl rounded-3xl shadow-2xl border border-white/20 p-12 flex flex-col items-center justify-center"
                    >
                      <div className="text-center">
                        <div className="inline-block px-4 py-2 bg-purple-100 text-purple-600 rounded-xl text-sm font-medium mb-6">
                          Question
                        </div>
                        <h2 className="text-3xl font-bold text-gray-800 mb-8">{currentCard.front}</h2>
                        <div className="text-gray-500 flex items-center justify-center gap-2">
                          <AlertCircle className="w-5 h-5" />
                          Click to reveal answer
                        </div>
                      </div>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="back"
                      initial={{ rotateY: 90 }}
                      animate={{ rotateY: 0 }}
                      exit={{ rotateY: -90 }}
                      transition={{ duration: 0.3 }}
                      className="absolute inset-0 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-3xl shadow-2xl p-12 flex flex-col"
                    >
                      <div className="flex-1 flex flex-col items-center justify-center">
                        <div className="inline-block px-4 py-2 bg-white/20 text-white rounded-xl text-sm font-medium mb-6">
                          Answer
                        </div>
                        <h2 className="text-3xl font-bold text-white text-center mb-8">
                          {currentCard.back}
                        </h2>
                      </div>

                      {/* Rating Buttons */}
                      <div className="grid grid-cols-4 gap-4">
                        {[
                          { label: 'Again', value: 'again', color: 'from-red-500 to-red-600', icon: RotateCcw },
                          { label: 'Hard', value: 'hard', color: 'from-orange-500 to-orange-600', icon: AlertCircle },
                          { label: 'Good', value: 'good', color: 'from-blue-500 to-blue-600', icon: Check },
                          { label: 'Easy', value: 'easy', color: 'from-green-500 to-green-600', icon: Zap },
                        ].map((rating) => (
                          <motion.button
                            key={rating.value}
                            whileHover={{ scale: 1.05, y: -5 }}
                            whileTap={{ scale: 0.95 }}
                            onClick={(e) => {
                              e.stopPropagation();
                              rateCard(rating.value as any);
                            }}
                            className={`py-4 bg-gradient-to-br ${rating.color} text-white rounded-2xl font-bold shadow-lg flex flex-col items-center gap-2`}
                          >
                            <rating.icon className="w-6 h-6" />
                            {rating.label}
                          </motion.button>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            )}

            {/* Keyboard Shortcuts Hint */}
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: 0.5 }}
              className="mt-6 bg-white/60 backdrop-blur-xl rounded-2xl p-4 border border-white/20"
            >
              <div className="flex items-center justify-center gap-8 text-sm text-gray-600">
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-gray-200 rounded text-xs font-mono">Space</kbd>
                  <span>Flip card</span>
                </div>
                <div className="flex items-center gap-2">
                  <kbd className="px-2 py-1 bg-gray-200 rounded text-xs font-mono">1-4</kbd>
                  <span>Rate card</span>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </AnimatePresence>
      )}
    </div>
  );
}
