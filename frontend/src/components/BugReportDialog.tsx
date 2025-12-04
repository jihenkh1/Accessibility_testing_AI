import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Alert, AlertDescription } from './ui/alert';
import { AlertCircle, Upload, X } from 'lucide-react';

const ALLOWED_FILE_TYPES = ['.png', '.jpg', '.jpeg', '.mp4', '.webm', '.wav', '.mp3'];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const MAX_FILES = 5;

const isValidFile = (file: File): boolean => {
  const ext = file.name.toLowerCase().match(/\.[^.]+$/)?.[0];
  return ALLOWED_FILE_TYPES.includes(ext || '') && file.size <= MAX_FILE_SIZE;
};

interface BugReportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  prefillData?: {
    wcagCriterion?: string;
    tool?: string;
    itemTitle?: string;
    projectName?: string;
  };
}

interface BugFormData {
  title: string;
  wcag_criterion: string;
  severity: string;
  testing_tool: string;
  description: string;
  expected_behavior: string;
  actual_behavior: string;
  steps_to_reproduce: string;
  affected_user_groups: string;
  notes: string;
  project_name: string;
}

export function BugReportDialog({ open, onOpenChange, prefillData }: BugReportDialogProps) {
  const queryClient = useQueryClient();
  const [formData, setFormData] = useState<BugFormData>({
    title: prefillData?.itemTitle || '',
    wcag_criterion: prefillData?.wcagCriterion || '',
    severity: 'Medium',
    testing_tool: prefillData?.tool?.toUpperCase() || 'NVDA',
    description: '',
    expected_behavior: '',
    actual_behavior: '',
    steps_to_reproduce: '',
    affected_user_groups: '',
    notes: '',
    project_name: prefillData?.projectName || 'Default Project',
  });
  const [evidenceFiles, setEvidenceFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);

  const createBugMutation = useMutation({
    mutationFn: async (data: BugFormData) => {
      const res = await axios.post('/api/manual-testing-v2/bugs', data);
      return res.data;
    },
    onSuccess: (bug) => {
      if (evidenceFiles.length > 0) {
        uploadEvidence(bug.id);
      } else {
        handleSuccess();
      }
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to create bug report');
    },
  });

  const uploadEvidence = async (bugId: number) => {
    try {
      for (const file of evidenceFiles) {
        const formData = new FormData();
        formData.append('file', file);
        await axios.post(`/api/manual-testing-v2/bugs/${bugId}/evidence`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }
      handleSuccess();
    } catch (err: any) {
      setError('Bug created but evidence upload failed');
    }
  };

  const handleSuccess = () => {
    queryClient.invalidateQueries({ queryKey: ['manual-bugs'] });
    queryClient.invalidateQueries({ queryKey: ['testing-method-stats'] });
    resetForm();
    onOpenChange(false);
  };

  const resetForm = () => {
    setFormData({
      title: '',
      wcag_criterion: '',
      severity: 'Medium',
      testing_tool: 'NVDA',
      description: '',
      expected_behavior: '',
      actual_behavior: '',
      steps_to_reproduce: '',
      affected_user_groups: '',
      notes: '',
      project_name: 'Default Project',
    });
    setEvidenceFiles([]);
    setError(null);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const validFiles = files.filter(isValidFile);
    setEvidenceFiles(prev => [...prev, ...validFiles].slice(0, MAX_FILES));
  };

  const removeFile = (index: number) => {
    setEvidenceFiles(prev => prev.filter((_, i) => i !== index));
  };

  const isFormValid = () => {
    return formData.title.trim() && 
           formData.wcag_criterion.trim() && 
           formData.description.trim() && 
           formData.expected_behavior.trim() && 
           formData.actual_behavior.trim();
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!isFormValid()) {
      setError('Please fill in all required fields');
      return;
    }

    createBugMutation.mutate(formData);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Report Accessibility Bug</DialogTitle>
          <DialogDescription>
            Document an accessibility issue found during manual testing
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2">
              <Label htmlFor="title">Bug Title *</Label>
              <Input
                id="title"
                value={formData.title}
                onChange={e => setFormData({ ...formData, title: e.target.value })}
                placeholder="Brief summary of the issue"
                required
              />
            </div>

            <div>
              <Label htmlFor="wcag">WCAG Criterion *</Label>
              <Input
                id="wcag"
                value={formData.wcag_criterion}
                onChange={e => setFormData({ ...formData, wcag_criterion: e.target.value })}
                placeholder="e.g., 1.1.1, 2.1.1"
                required
              />
            </div>

            <div>
              <Label htmlFor="severity">Severity *</Label>
              <Select
                value={formData.severity}
                onValueChange={value => setFormData({ ...formData, severity: value })}
              >
                <SelectTrigger id="severity">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="Critical">Critical - Blocker</SelectItem>
                  <SelectItem value="High">High - Major issue</SelectItem>
                  <SelectItem value="Medium">Medium - Moderate</SelectItem>
                  <SelectItem value="Low">Low - Minor</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="tool">Testing Tool *</Label>
              <Select
                value={formData.testing_tool}
                onValueChange={value => setFormData({ ...formData, testing_tool: value })}
              >
                <SelectTrigger id="tool">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="NVDA">NVDA Screen Reader</SelectItem>
                  <SelectItem value="Keyboard">Keyboard Navigation</SelectItem>
                  <SelectItem value="Zoom">Zoom/Low Vision</SelectItem>
                  <SelectItem value="Other">Other Tool</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="project">Project</Label>
              <Input
                id="project"
                value={formData.project_name}
                onChange={e => setFormData({ ...formData, project_name: e.target.value })}
                placeholder="Project name"
              />
            </div>
          </div>

          <div>
            <Label htmlFor="description">What is Broken? *</Label>
            <Textarea
              id="description"
              value={formData.description}
              onChange={e => setFormData({ ...formData, description: e.target.value })}
              placeholder="Describe the accessibility issue"
              rows={3}
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="expected">Expected Behavior *</Label>
              <Textarea
                id="expected"
                value={formData.expected_behavior}
                onChange={e => setFormData({ ...formData, expected_behavior: e.target.value })}
                placeholder="What should happen?"
                rows={3}
                required
              />
            </div>

            <div>
              <Label htmlFor="actual">Actual Behavior *</Label>
              <Textarea
                id="actual"
                value={formData.actual_behavior}
                onChange={e => setFormData({ ...formData, actual_behavior: e.target.value })}
                placeholder="What actually happens?"
                rows={3}
                required
              />
            </div>
          </div>

          <div>
            <Label htmlFor="steps">Steps to Reproduce</Label>
            <Textarea
              id="steps"
              value={formData.steps_to_reproduce}
              onChange={e => setFormData({ ...formData, steps_to_reproduce: e.target.value })}
              placeholder="1. Navigate to...\n2. Activate...\n3. Observe..."
              rows={3}
            />
          </div>

          <div>
            <Label htmlFor="affected">Affected User Groups</Label>
            <Input
              id="affected"
              value={formData.affected_user_groups}
              onChange={e => setFormData({ ...formData, affected_user_groups: e.target.value })}
              placeholder="e.g., Screen reader users, Keyboard-only users"
            />
          </div>

          <div>
            <Label htmlFor="notes">Additional Notes</Label>
            <Textarea
              id="notes"
              value={formData.notes}
              onChange={e => setFormData({ ...formData, notes: e.target.value })}
              placeholder="Any other relevant information"
              rows={2}
            />
          </div>

          <div>
            <Label htmlFor="evidence">Evidence (Images, Videos, Audio)</Label>
            <div className="mt-2">
              <label
                htmlFor="evidence"
                className="flex items-center justify-center w-full p-4 border-2 border-dashed rounded-lg cursor-pointer hover:bg-accent"
              >
                <Upload className="w-5 h-5 mr-2" />
                <span className="text-sm">Upload files (max 10MB, up to 5 files)</span>
                <input
                  id="evidence"
                  type="file"
                  multiple
                  accept=".png,.jpg,.jpeg,.mp4,.webm,.wav,.mp3"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
            </div>
            {evidenceFiles.length > 0 && (
              <div className="mt-2 space-y-2">
                {evidenceFiles.map((file, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-accent rounded">
                    <span className="text-sm truncate">{file.name}</span>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onClick={() => removeFile(index)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="flex justify-end gap-2 pt-4">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={createBugMutation.isPending}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={createBugMutation.isPending}>
              {createBugMutation.isPending ? 'Creating...' : 'Create Bug Report'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  );
}
