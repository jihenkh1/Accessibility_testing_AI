import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Alert, AlertDescription } from '../components/ui/alert';
import { ArrowLeft, ExternalLink, Download, FileText, Image, Video, Music, AlertCircle, ClipboardCopy } from 'lucide-react';
import { toast } from 'sonner';

interface BugDetail {
  id: number;
  title: string;
  wcag_criterion: string;
  severity: string;
  testing_tool: string;
  description: string;
  expected_behavior: string;
  actual_behavior: string;
  steps_to_reproduce: string | null;
  affected_user_groups: string | null;
  notes: string | null;
  project_name: string;
  run_id: number | null;
  created_at: string;
  created_by: string | null;
  evidence: Array<{
    id: number;
    file_path: string;
    file_type: string;
    file_size: number;
    uploaded_at: string;
  }>;
}

const bugApi = {
  fetch: (id: string) => axios.get(`/api/manual-testing-v2/bugs/${id}`).then((res) => res.data),
  delete: (id: string) => axios.delete(`/api/manual-testing-v2/bugs/${id}`).then((res) => res.data),
};

const getFileIcon = (fileType: string) => {
  if (fileType.startsWith('image')) return <Image className="w-4 h-4" />;
  if (fileType.startsWith('video')) return <Video className="w-4 h-4" />;
  if (fileType.startsWith('audio')) return <Music className="w-4 h-4" />;
  return <FileText className="w-4 h-4" />;
};

const formatFileSize = (bytes: number) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

const buildJiraTemplate = (bug: BugDetail) => {
  const lines: string[] = [];

  lines.push(`h2. Accessibility Bug Report`);
  lines.push(`*Title:* ${bug.title}`);
  lines.push(`*Project:* ${bug.project_name}`);
  lines.push(`*Severity:* ${bug.severity}`);
  lines.push(`*WCAG:* ${bug.wcag_criterion}`);
  lines.push(`*Testing tool:* ${bug.testing_tool}`);
  if (bug.created_by) lines.push(`*Reported by:* ${bug.created_by}`);
  lines.push(`*Reported at:* ${new Date(bug.created_at).toLocaleString()}`);

  if (bug.run_id) lines.push(`*Related scan:* #${bug.run_id}`);

  lines.push('');
  lines.push(`h3. What is broken`);
  lines.push(bug.description || '-');

  lines.push('');
  lines.push(`h3. Expected behavior`);
  lines.push(bug.expected_behavior || '-');

  lines.push('');
  lines.push(`h3. Actual behavior`);
  lines.push(bug.actual_behavior || '-');

  lines.push('');
  lines.push(`h3. Steps to reproduce`);
  lines.push(
    bug.steps_to_reproduce?.trim()
      ? bug.steps_to_reproduce
      : 'Not provided (manual review required)'
  );

  if (bug.affected_user_groups?.trim()) {
    lines.push('');
    lines.push(`h3. Affected users`);
    lines.push(bug.affected_user_groups);
  }

  if (bug.notes?.trim()) {
    lines.push('');
    lines.push(`h3. Additional notes`);
    lines.push(bug.notes);
  }

  if (bug.evidence?.length) {
    lines.push('');
    lines.push(`h3. Evidence`);
    bug.evidence.forEach((ev) => {
      const filename = ev.file_path.split('/').pop() || ev.file_path;
      const downloadUrl = `${window.location.origin}/api/manual-testing-v2/bugs/${bug.id}/evidence/${ev.id}/download`;
      lines.push(`- ${filename} (${ev.file_type}, ${formatFileSize(ev.file_size)}): ${downloadUrl}`);
    });
  }

  lines.push('');
  lines.push(`---`);
  lines.push(`Generated from AccessTest (Manual Testing)`);

  return lines.join('\n');
};

const severityColors: Record<string, 'destructive' | 'default' | 'secondary'> = {
  Critical: 'destructive',
  High: 'destructive',
  Medium: 'default',
  Low: 'secondary',
};

const getErrorMessage = (err: any, fallback: string) => {
  const detail = err?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map((d: any) => d?.msg).filter(Boolean).join(', ');
  return fallback;
};

export default function BugDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const { data: bug, isLoading } = useQuery({
    queryKey: ['bug', id],
    queryFn: () => bugApi.fetch(id!),
    enabled: !!id,
  });
  const deleteMutation = useMutation({
    mutationFn: () => bugApi.delete(id!),
    onSuccess: () => navigate('/manual-testing-v2/bugs'),
    onError: (err: any) => setError(getErrorMessage(err, 'Failed to delete bug')),
  });

  const handleDelete = () => {
    if (confirm('Are you sure you want to delete this bug? This cannot be undone.')) {
      deleteMutation.mutate();
    }
  };

  const handleCopyForJira = async () => {
    if (!bug) return;
    const jiraText = buildJiraTemplate(bug);
    try {
      if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(jiraText);
      } else {
        const textarea = document.createElement('textarea');
        textarea.value = jiraText;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
      }
      toast.success('Copied Jira-ready summary');
    } catch (copyError) {
      console.error(copyError);
      toast.error('Unable to copy bug details');
    }
  };

  if (isLoading) return <div className="p-6 text-muted-foreground">Loading bug details...</div>;
  if (!bug) return <div className="p-6 text-muted-foreground">Bug not found</div>;

  return (
    <div className="p-6 max-w-[1200px] mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/manual-testing-v2/bugs')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to List
          </Button>
          <div>
            <h1 className="text-2xl font-bold">Bug #{bug.id}</h1>
            <p className="text-sm text-muted-foreground">
              Created {new Date(bug.created_at).toLocaleString()}
              {bug.created_by && ` by ${bug.created_by}`}
            </p>
          </div>
        </div>
        <Button variant="destructive" onClick={handleDelete} disabled={deleteMutation.isPending}>
          {deleteMutation.isPending ? 'Deleting...' : 'Delete Bug'}
        </Button>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>{bug.title}</CardTitle>
              <div className="flex gap-2 mt-2">
                <Badge variant={severityColors[bug.severity] as any}>{bug.severity}</Badge>
                <Badge variant="outline">{bug.wcag_criterion}</Badge>
                <Badge variant="secondary">{bug.testing_tool}</Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <h3 className="font-semibold mb-2">Description</h3>
                <p className="text-sm text-muted-foreground whitespace-pre-wrap">{bug.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h3 className="font-semibold mb-2">Expected Behavior</h3>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">{bug.expected_behavior}</p>
                </div>
                <div>
                  <h3 className="font-semibold mb-2">Actual Behavior</h3>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">{bug.actual_behavior}</p>
                </div>
              </div>

              {bug.steps_to_reproduce && (
                <div>
                  <h3 className="font-semibold mb-2">Steps to Reproduce</h3>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">{bug.steps_to_reproduce}</p>
                </div>
              )}

              {bug.affected_user_groups && (
                <div>
                  <h3 className="font-semibold mb-2">Affected User Groups</h3>
                  <p className="text-sm text-muted-foreground">{bug.affected_user_groups}</p>
                </div>
              )}

              {bug.notes && (
                <div>
                  <h3 className="font-semibold mb-2">Additional Notes</h3>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap">{bug.notes}</p>
                </div>
              )}
            </CardContent>
          </Card>

          {bug.evidence.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Evidence ({bug.evidence.length})</CardTitle>
                <CardDescription>Attached screenshots, videos, and audio files</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {bug.evidence.map((file: any) => (
                    <div
                      key={file.id}
                      className="flex items-center justify-between p-3 border rounded-lg hover:bg-accent"
                    >
                      <div className="flex items-center gap-3">
                        {getFileIcon(file.file_type)}
                        <div>
                          <p className="text-sm font-medium">{file.file_path.split('/').pop()}</p>
                          <p className="text-xs text-muted-foreground">
                            {formatFileSize(file.file_size)} • {new Date(file.uploaded_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          window.open(
                            `/api/manual-testing-v2/bugs/${bug.id}/evidence/${file.id}/download`,
                            '_blank'
                          )
                        }
                      >
                        <Download className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Share with Jira</CardTitle>
              <CardDescription>Copy a structured summary for an external ticket</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button
                variant="outline"
                size="sm"
                className="w-full justify-center gap-2"
                onClick={handleCopyForJira}
              >
                <ClipboardCopy className="w-4 h-4" />
                Copy for Jira
              </Button>
              <p className="text-xs text-muted-foreground">
                Includes severity, WCAG reference, expected vs. actual behaviour, and reproduction steps.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <p className="text-muted-foreground">Project</p>
                <p className="font-medium">{bug.project_name}</p>
              </div>

              {bug.run_id && (
                <div>
                  <p className="text-muted-foreground">Related Scan</p>
                  <Button
                    variant="link"
                    className="p-0 h-auto"
                    onClick={() => navigate(`/scan/${bug.run_id}`)}
                  >
                    View Scan #{bug.run_id}
                    <ExternalLink className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              )}

              <div>
                <p className="text-muted-foreground">WCAG Reference</p>
                <Button
                  variant="link"
                  className="p-0 h-auto"
                  onClick={() =>
                    window.open(
                      `https://www.w3.org/WAI/WCAG21/Understanding/${bug.wcag_criterion.replace('.', '')}.html`,
                      '_blank'
                    )
                  }
                >
                  Understanding {bug.wcag_criterion}
                  <ExternalLink className="w-3 h-3 ml-1" />
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
