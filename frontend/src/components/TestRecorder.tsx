import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Textarea } from './ui/textarea';
import { Progress } from './ui/progress';
import { CheckCircle2, XCircle, RotateCw, SkipForward, Upload, ChevronLeft, ChevronRight } from 'lucide-react';

interface ChecklistItem {
  id: string;
  category: string;
  title?: string; // Legacy field
  description?: string; // Legacy field
  wcag?: string; // Legacy field
  test_item?: string; // New actionable test instruction
  how_to_test?: string; // Step-by-step instructions
  what_to_look_for?: string; // Success criteria
  wcag_reference?: string; // WCAG guideline
  priority: string;
  estimated_time?: number; // Time estimate in minutes
}

interface TestResult {
  item_id: string;
  status: string;
  notes?: string;
}

interface SessionData {
  session: {
    id: number;
    tester_name: string;
    started_at: string;
    status: string;
  };
  checklist: {
    checklist_id: number;
    page_type: string;
    items: ChecklistItem[];
    total_items: number;
  };
  results: TestResult[];
  progress: {
    passed: number;
    failed: number;
    needs_retest: number;
    skipped: number;
    total: number;
  };
}

export function TestRecorder() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [sessionData, setSessionData] = useState<SessionData | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [notes, setNotes] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadSessionData();
  }, [sessionId]);

  const loadSessionData = async () => {
    try {
      const res = await fetch(`/api/manual-testing/sessions/${sessionId}/results`);
      if (!res.ok) throw new Error('Failed to load session');
      const data = await res.json();
      setSessionData(data);
    } catch (error) {
      console.error('Error loading session:', error);
      alert('Failed to load testing session');
    } finally {
      setIsLoading(false);
    }
  };

  const recordResult = async (status: string) => {
    if (!sessionData) return;

    const currentItem = sessionData.checklist.items[currentIndex];
    setIsSubmitting(true);

    try {
      const res = await fetch('/api/manual-testing/tests/record', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionData.session.id,
          item_id: currentItem.id,
          status,
          notes: notes.trim() || null
        })
      });

      if (!res.ok) throw new Error('Failed to record result');

      // Reload session data to update progress
      await loadSessionData();

      // Clear notes
      setNotes('');
      
      // Only move to next item if not at the end
      if (currentIndex < sessionData.checklist.items.length - 1) {
        setCurrentIndex(currentIndex + 1);
      } else {
        // At the last item - optionally prompt to complete session
        const confirmComplete = window.confirm('You have completed all test items! Would you like to mark this session as complete?');
        if (confirmComplete) {
          await handleComplete();
        }
      }
    } catch (error) {
      console.error('Error recording result:', error);
      alert('Failed to record test result');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleComplete = async () => {
    if (!sessionData) return;

    try {
      const res = await fetch(`/api/manual-testing/sessions/${sessionData.session.id}/complete`, {
        method: 'PUT'
      });

      if (!res.ok) throw new Error('Failed to complete session');

      alert('Testing session completed!');
      navigate('/manual-testing/sessions');
    } catch (error) {
      console.error('Error completing session:', error);
      alert('Failed to complete session');
    }
  };

  if (isLoading) {
    return <div className="p-8 text-center">Loading testing session...</div>;
  }

  if (!sessionData) {
    return <div className="p-8 text-center">Session not found</div>;
  }

  const currentItem = sessionData.checklist.items[currentIndex];
  const completedCount =
    sessionData.progress.passed +
    sessionData.progress.failed +
    sessionData.progress.needs_retest +
    sessionData.progress.skipped;
  const progressPercent = (completedCount / sessionData.progress.total) * 100;
  const isAllComplete = completedCount === sessionData.progress.total;

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'bg-destructive text-destructive-foreground';
      case 'high':
        return 'bg-orange-500 text-white';
      case 'medium':
        return 'bg-yellow-500 text-white';
      default:
        return 'bg-blue-500 text-white';
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Manual Testing Session</h1>
          <p className="text-muted-foreground mt-1">
            Tester: {sessionData.session.tester_name} • Page Type: {sessionData.checklist.page_type}
          </p>
        </div>
        <Button onClick={handleComplete} variant="outline">
          Complete Session
        </Button>
      </div>

      {/* Progress Overview */}
      <Card>
        <CardContent className="pt-6">
          <div className="space-y-4">
            {isAllComplete && (
              <div className="bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded-lg p-4 mb-4">
                <div className="flex items-center gap-2 text-green-700 dark:text-green-300">
                  <CheckCircle2 className="w-5 h-5" />
                  <span className="font-medium">All tests completed! You can now complete the session.</span>
                </div>
              </div>
            )}
            <div className="flex justify-between text-sm">
              <span>Progress: {completedCount} / {sessionData.progress.total} items</span>
              <span>{Math.round(progressPercent)}%</span>
            </div>
            <Progress value={progressPercent} className="h-2" />
            <div className="flex gap-4 text-sm">
              <div className="flex items-center gap-1">
                <CheckCircle2 className="w-4 h-4 text-green-500" />
                <span>{sessionData.progress.passed} passed</span>
              </div>
              <div className="flex items-center gap-1">
                <XCircle className="w-4 h-4 text-destructive" />
                <span>{sessionData.progress.failed} failed</span>
              </div>
              <div className="flex items-center gap-1">
                <RotateCw className="w-4 h-4 text-orange-500" />
                <span>{sessionData.progress.needs_retest} needs retest</span>
              </div>
              <div className="flex items-center gap-1">
                <SkipForward className="w-4 h-4 text-muted-foreground" />
                <span>{sessionData.progress.skipped} skipped</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current Test Item */}
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-2 flex-1">
              <div className="flex items-center gap-2">
                <Badge className={getPriorityColor(currentItem.priority)}>
                  {currentItem.priority}
                </Badge>
                <Badge variant="outline">{currentItem.category}</Badge>
                <span className="text-sm text-muted-foreground">
                  {currentIndex + 1} of {sessionData.checklist.items.length}
                </span>
                {currentItem.estimated_time && (
                  <span className="text-sm text-muted-foreground">
                    ⏱️ ~{currentItem.estimated_time} min
                  </span>
                )}
              </div>
              <CardTitle className="text-xl">
                {currentItem.test_item || currentItem.title}
              </CardTitle>
              {currentItem.description && !currentItem.test_item && (
                <CardDescription className="text-base">{currentItem.description}</CardDescription>
              )}
            </div>
          </div>
          <div className="mt-4 text-sm text-muted-foreground">
            WCAG Reference: {currentItem.wcag_reference || currentItem.wcag}
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* How to Test - Step by step instructions */}
          {currentItem.how_to_test && (
            <div className="space-y-2 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg border border-blue-200 dark:border-blue-800">
              <h3 className="text-sm font-semibold text-blue-900 dark:text-blue-100">
                📋 How to Test
              </h3>
              <pre className="text-sm text-blue-800 dark:text-blue-200 whitespace-pre-wrap font-sans">
                {currentItem.how_to_test}
              </pre>
            </div>
          )}

          {/* What to Look For - Success criteria */}
          {currentItem.what_to_look_for && (
            <div className="space-y-2 p-4 bg-green-50 dark:bg-green-950 rounded-lg border border-green-200 dark:border-green-800">
              <h3 className="text-sm font-semibold text-green-900 dark:text-green-100">
                ✓ What to Look For
              </h3>
              <pre className="text-sm text-green-800 dark:text-green-200 whitespace-pre-wrap font-sans">
                {currentItem.what_to_look_for}
              </pre>
            </div>
          )}

          {/* Notes */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Notes (optional)</label>
            <Textarea
              placeholder="Add any observations, issues found, or additional context..."
              value={notes}
              onChange={e => setNotes(e.target.value)}
              rows={4}
            />
          </div>

          {/* Action Buttons */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Button
              onClick={() => recordResult('passed')}
              disabled={isSubmitting}
              className="bg-green-600 hover:bg-green-700 text-white"
            >
              <CheckCircle2 className="w-4 h-4 mr-2" />
              Pass
            </Button>
            <Button
              onClick={() => recordResult('failed')}
              disabled={isSubmitting}
              variant="destructive"
            >
              <XCircle className="w-4 h-4 mr-2" />
              Fail
            </Button>
            <Button
              onClick={() => recordResult('needs_retest')}
              disabled={isSubmitting}
              className="bg-orange-600 hover:bg-orange-700 text-white"
            >
              <RotateCw className="w-4 h-4 mr-2" />
              Retest
            </Button>
            <Button
              onClick={() => recordResult('skipped')}
              disabled={isSubmitting}
              variant="outline"
            >
              <SkipForward className="w-4 h-4 mr-2" />
              Skip
            </Button>
          </div>

          {/* Navigation */}
          <div className="flex justify-between pt-4 border-t">
            <Button
              onClick={() => setCurrentIndex(Math.max(0, currentIndex - 1))}
              disabled={currentIndex === 0}
              variant="outline"
              size="sm"
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              Previous
            </Button>
            <Button
              onClick={() => setCurrentIndex(Math.min(sessionData.checklist.items.length - 1, currentIndex + 1))}
              disabled={currentIndex === sessionData.checklist.items.length - 1}
              variant="outline"
              size="sm"
            >
              Next
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Screenshot Upload (future enhancement) */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Evidence & Screenshots</CardTitle>
          <CardDescription>Upload screenshots or additional evidence (coming soon)</CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="outline" disabled>
            <Upload className="w-4 h-4 mr-2" />
            Upload Screenshot
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
