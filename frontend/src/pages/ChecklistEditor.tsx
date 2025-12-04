import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Textarea } from '../components/ui/textarea';
import { Badge } from '../components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../components/ui/table';
import { AlertCircle, Plus, Trash2, Save, Download, X, ArrowLeft } from 'lucide-react';
import { Alert, AlertDescription } from '../components/ui/alert';
import { toast } from 'sonner';

interface ChecklistItem {
  wcag_criterion: string;
  level: string;
  item_title: string;
  instructions: string;
  expected_result: string;
  common_failures: string;
  tool: string;
  priority: string;
  reference_url: string;
}

// Consolidated API calls
const checklistApi = {
  fetch: async (tool: string) => {
    const res = await axios.get(`/api/manual-testing-v2/checklists/${tool}`);
    return res.data;
  },
  save: async (tool: string, items: ChecklistItem[]) => {
    const res = await axios.put(`/api/manual-testing-v2/checklists/${tool}`, items);
    return res.data;
  }
};

export default function ChecklistEditor() {
  const { tool } = useParams<{ tool: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [items, setItems] = useState<ChecklistItem[]>([]);
  const [editingIndex, setEditingIndex] = useState<number | null>(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { data: checklist, isLoading } = useQuery({
    queryKey: ['checklist', tool],
    queryFn: () => checklistApi.fetch(tool!),
    enabled: !!tool
  });

  const saveMutation = useMutation({
    mutationFn: (items: ChecklistItem[]) => checklistApi.save(tool!, items),
    onSuccess: () => {
      setHasChanges(false);
      setError(null);
      queryClient.invalidateQueries({ queryKey: ['checklist', tool] });
      toast.success('Checklist saved successfully!');
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to save checklist');
    }
  });

  useEffect(() => {
    if (checklist?.checklist_items) {
      setItems(checklist.checklist_items);
    }
  }, [checklist]);

  const handleAddRow = () => {
    const newItem: ChecklistItem = {
      wcag_criterion: '',
      level: 'A',
      item_title: '',
      instructions: '',
      expected_result: '',
      common_failures: '',
      tool: tool?.toUpperCase() || 'NVDA',
      priority: 'Medium',
      reference_url: ''
    };
    setItems([...items, newItem]);
    setEditingIndex(items.length);
    setHasChanges(true);
  };

  const handleDeleteRow = (index: number) => {
    const confirmed = window.confirm('Are you sure you want to delete this checklist item?');
    if (confirmed) {
      setItems(items.filter((_, i) => i !== index));
      setHasChanges(true);
      if (editingIndex === index) {
        setEditingIndex(null);
      }
      toast.success('Checklist item deleted');
    }
  };

  const handleUpdateItem = (index: number, field: keyof ChecklistItem, value: string) => {
    const updated = [...items];
    updated[index] = { ...updated[index], [field]: value };
    setItems(updated);
    setHasChanges(true);
  };

  const handleSave = () => {
    // Validate all items
    const invalid = items.find((item, idx) => {
      return !item.wcag_criterion || !item.item_title || !item.instructions || !item.expected_result;
    });

    if (invalid) {
      setError('Please fill in all required fields (WCAG Criterion, Title, Instructions, Expected Result)');
      return;
    }

    saveMutation.mutate(items);
  };

  const handleDownload = () => {
    window.open(`/api/manual-testing-v2/checklists/${tool}/download`, '_blank');
  };

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="text-muted-foreground">Loading checklist...</div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-[1600px] mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/manual-testing')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>
          <div>
            <h1 className="text-3xl font-bold">{checklist?.name || 'Checklist Editor'}</h1>
            <p className="text-muted-foreground">
              Edit checklist items • {items.length} items
              {hasChanges && <span className="text-orange-600 ml-2">• Unsaved changes</span>}
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleDownload}>
            <Download className="w-4 h-4 mr-2" />
            Download Excel
          </Button>
          <Button onClick={handleAddRow}>
            <Plus className="w-4 h-4 mr-2" />
            Add Item
          </Button>
          <Button 
            onClick={handleSave} 
            disabled={!hasChanges || saveMutation.isPending}
            variant="default"
          >
            <Save className="w-4 h-4 mr-2" />
            {saveMutation.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>

      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
          <Button variant="ghost" size="sm" onClick={() => setError(null)} className="absolute right-2 top-2">
            <X className="w-4 h-4" />
          </Button>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Checklist Items</CardTitle>
          <CardDescription>
            Click on any row to edit. All fields are editable except the tool name.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="border rounded-lg overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-[100px]">WCAG</TableHead>
                  <TableHead className="w-[60px]">Level</TableHead>
                  <TableHead className="w-[250px]">Title</TableHead>
                  <TableHead className="w-[300px]">Instructions</TableHead>
                  <TableHead className="w-[200px]">Expected Result</TableHead>
                  <TableHead className="w-[200px]">Common Failures</TableHead>
                  <TableHead className="w-[80px]">Tool</TableHead>
                  <TableHead className="w-[100px]">Priority</TableHead>
                  <TableHead className="w-[200px]">Reference URL</TableHead>
                  <TableHead className="w-[80px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((item, index) => (
                  <TableRow 
                    key={index}
                    className={editingIndex === index ? 'bg-accent' : 'hover:bg-muted/50 cursor-pointer'}
                    onClick={() => editingIndex !== index && setEditingIndex(index)}
                  >
                    <TableCell>
                      {editingIndex === index ? (
                        <Input
                          value={item.wcag_criterion}
                          onChange={(e) => handleUpdateItem(index, 'wcag_criterion', e.target.value)}
                          placeholder="1.1.1"
                          className="h-8"
                        />
                      ) : (
                        <Badge variant="outline">{item.wcag_criterion}</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {editingIndex === index ? (
                        <Select
                          value={item.level}
                          onValueChange={(value) => handleUpdateItem(index, 'level', value)}
                        >
                          <SelectTrigger className="h-8">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="A">A</SelectItem>
                            <SelectItem value="AA">AA</SelectItem>
                            <SelectItem value="AAA">AAA</SelectItem>
                          </SelectContent>
                        </Select>
                      ) : (
                        <Badge variant="secondary">{item.level}</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {editingIndex === index ? (
                        <Input
                          value={item.item_title}
                          onChange={(e) => handleUpdateItem(index, 'item_title', e.target.value)}
                          placeholder="Item title"
                          className="h-8"
                        />
                      ) : (
                        <span className="text-sm font-medium">{item.item_title}</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {editingIndex === index ? (
                        <Textarea
                          value={item.instructions}
                          onChange={(e) => handleUpdateItem(index, 'instructions', e.target.value)}
                          placeholder="Testing instructions..."
                          className="min-h-[60px]"
                        />
                      ) : (
                        <span className="text-sm text-muted-foreground line-clamp-2">{item.instructions}</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {editingIndex === index ? (
                        <Textarea
                          value={item.expected_result}
                          onChange={(e) => handleUpdateItem(index, 'expected_result', e.target.value)}
                          placeholder="Expected result..."
                          className="min-h-[60px]"
                        />
                      ) : (
                        <span className="text-sm text-muted-foreground line-clamp-2">{item.expected_result}</span>
                      )}
                    </TableCell>
                    <TableCell>
                      {editingIndex === index ? (
                        <Textarea
                          value={item.common_failures}
                          onChange={(e) => handleUpdateItem(index, 'common_failures', e.target.value)}
                          placeholder="Common failures..."
                          className="min-h-[60px]"
                        />
                      ) : (
                        <span className="text-sm text-muted-foreground line-clamp-2">{item.common_failures}</span>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">{item.tool}</Badge>
                    </TableCell>
                    <TableCell>
                      {editingIndex === index ? (
                        <Select
                          value={item.priority}
                          onValueChange={(value) => handleUpdateItem(index, 'priority', value)}
                        >
                          <SelectTrigger className="h-8">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="Critical">Critical</SelectItem>
                            <SelectItem value="High">High</SelectItem>
                            <SelectItem value="Medium">Medium</SelectItem>
                            <SelectItem value="Low">Low</SelectItem>
                          </SelectContent>
                        </Select>
                      ) : (
                        <Badge variant={item.priority === 'Critical' ? 'destructive' : 'default'}>
                          {item.priority}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {editingIndex === index ? (
                        <Input
                          value={item.reference_url}
                          onChange={(e) => handleUpdateItem(index, 'reference_url', e.target.value)}
                          placeholder="https://..."
                          className="h-8"
                        />
                      ) : (
                        item.reference_url ? (
                          <a
                            href={item.reference_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            Link →
                          </a>
                        ) : (
                          <span className="text-xs text-muted-foreground">-</span>
                        )
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        {editingIndex === index && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={(e) => {
                              e.stopPropagation();
                              setEditingIndex(null);
                            }}
                          >
                            Done
                          </Button>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDeleteRow(index);
                          }}
                        >
                          <Trash2 className="w-4 h-4 text-destructive" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {items.length === 0 && (
            <div className="text-center py-12 text-muted-foreground">
              <p>No checklist items yet.</p>
              <Button onClick={handleAddRow} className="mt-4">
                <Plus className="w-4 h-4 mr-2" />
                Add First Item
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
