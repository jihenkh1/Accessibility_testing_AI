import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Badge } from './ui/badge';
import { Checkbox } from './ui/checkbox';
import { Input } from './ui/input';

interface ChecklistWizardProps {
  runId?: number;
}

interface PageTypeOption {
  value: string;
  label: string;
  description: string;
}

interface ComponentOption {
  value: string;
  label: string;
}

const PAGE_TYPES: PageTypeOption[] = [
  {
    value: 'content_articles',
    label: '🎯 Information & Discovery',
    description: 'Finding content, learning, researching, browsing\nExamples: News articles, blogs, documentation, help centers\nKey tests: Reading order, content structure, navigation, search'
  },
  {
    value: 'forms_data_input',
    label: '📝 Data Entry & Forms',
    description: 'Providing information, completing tasks, submitting data\nExamples: Login, registration, contact forms, applications\nKey tests: Form labels, validation, error handling, submission'
  },
  {
    value: 'data_display',
    label: '📊 Data Analysis & Monitoring',
    description: 'Viewing information, monitoring status, making decisions\nExamples: Dashboards, analytics, admin panels, reports\nKey tests: Data tables, charts, filters, keyboard navigation'
  },
  {
    value: 'ecommerce_checkout',
    label: '🛒 Transactions & Commerce',
    description: 'Making purchases, managing accounts, financial actions\nExamples: E-commerce, banking, booking systems, payments\nKey tests: Multi-step flows, form security, confirmation'
  },
  {
    value: 'user_account',
    label: '⚙️ Management & Configuration',
    description: 'Managing settings, preferences, user accounts\nExamples: User profiles, admin settings, preferences\nKey tests: Complex forms, data management, permission controls'
  },
  {
    value: 'search_results',
    label: '🔍 Navigation & Search',
    description: 'Finding content, moving between sections, wayfinding\nExamples: Site navigation, search results, menus\nKey tests: Menu access, search functionality, breadcrumbs'
  }
];

interface ComponentGroup {
  title: string;
  description: string;
  components: ComponentOption[];
}

const COMPONENT_GROUPS: ComponentGroup[] = [
  {
    title: 'Navigation & Menus',
    description: 'Main navigation, dropdown menus, sidebars, breadcrumbs, pagination, progress indicators',
    components: [
      { value: 'menu', label: 'Navigation Menus' },
      { value: 'dropdown', label: 'Dropdown Menus' },
      { value: 'pagination', label: 'Pagination' }
    ]
  },
  {
    title: 'Forms & Inputs',
    description: 'Text inputs, dropdowns, checkboxes, radio buttons, file uploads, date pickers, search boxes, auto-complete, filters',
    components: [
      { value: 'datepicker', label: 'Date Pickers' },
      { value: 'search', label: 'Search Boxes' }
    ]
  },
  {
    title: 'Data Display',
    description: 'Data tables with sorting/filtering, charts, graphs, data visualizations, lists, grids, card layouts',
    components: []
  },
  {
    title: 'Media & Content',
    description: 'Image galleries, carousels, lightboxes, video/audio players with controls, embedded content (maps, social media)',
    components: [
      { value: 'carousel', label: 'Carousels/Sliders' }
    ]
  },
  {
    title: 'Interactive Widgets',
    description: 'Modals, dialogs, popovers, tooltips, accordions, tabs, expandable sections, notifications, alerts, status messages',
    components: [
      { value: 'modal', label: 'Modals/Dialogs' },
      { value: 'tooltip', label: 'Tooltips/Popovers' },
      { value: 'tabs', label: 'Tabs' },
      { value: 'accordion', label: 'Accordions' }
    ]
  },
  {
    title: 'Dynamic Content',
    description: 'Live updates, real-time data, infinite scroll, lazy loading, auto-saving, progress indicators',
    components: []
  },
  {
    title: 'Mobile & Touch',
    description: 'Swipeable content, touch gestures, mobile navigation, bottom bars, responsive layouts, zoom interactions',
    components: []
  }
];

export function ChecklistWizard({ runId }: ChecklistWizardProps) {
  const navigate = useNavigate();
  const [pageType, setPageType] = useState<string>('');
  const [selectedComponents, setSelectedComponents] = useState<string[]>([]);
  const [testerName, setTesterName] = useState('');
  const [detectedComponents, setDetectedComponents] = useState<string[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);
  const [step, setStep] = useState(1);

  // Auto-detect components if runId provided
  useEffect(() => {
    if (runId) {
      fetch(`/api/manual-testing/runs/${runId}/detect-components`)
        .then(res => res.json())
        .then(data => {
          setDetectedComponents(data.components || []);
          setSelectedComponents(data.components || []);
        })
        .catch(err => console.error('Failed to detect components:', err));
    }
  }, [runId]);

  const toggleComponent = (component: string) => {
    setSelectedComponents(prev =>
      prev.includes(component)
        ? prev.filter(c => c !== component)
        : [...prev, component]
    );
  };

  const handleGenerate = async () => {
    if (!pageType || !testerName) {
      alert('Please select page type and enter your name');
      return;
    }

    setIsGenerating(true);
    try {
      // Generate checklist
      const checklistRes = await fetch('/api/manual-testing/checklists/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          page_type: pageType,
          components: selectedComponents,
          run_id: runId
        })
      });

      if (!checklistRes.ok) {
        throw new Error('Failed to generate checklist');
      }

      const checklist = await checklistRes.json();

      // Create test session
      const sessionRes = await fetch('/api/manual-testing/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          checklist_id: checklist.checklist_id,
          tester_name: testerName,
          run_id: runId
        })
      });

      if (!sessionRes.ok) {
        throw new Error('Failed to create session');
      }

      const session = await sessionRes.json();

      // Navigate to testing interface
      navigate(`/manual-testing/session/${session.id}`);
    } catch (error) {
      console.error('Error generating checklist:', error);
      alert('Failed to generate checklist. Please try again.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 p-6">
      {/* Header */}
      <div className="text-center space-y-2 mb-8">
        <h1 className="text-3xl font-bold">Create Accessibility Test Session</h1>
        <p className="text-muted-foreground text-lg">
          Define what you're testing to get targeted, actionable checklists
        </p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center justify-center gap-4 mb-8">
        <div className={`flex items-center gap-2 ${step >= 1 ? 'text-primary' : 'text-muted-foreground'}`}>
          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${step >= 1 ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
            {step > 1 ? '✓' : '1'}
          </div>
          <span className="font-medium">User Goal</span>
        </div>
        <div className="w-16 h-px bg-border"></div>
        <div className={`flex items-center gap-2 ${step >= 2 ? 'text-primary' : 'text-muted-foreground'}`}>
          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${step >= 2 ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
            {step > 2 ? '✓' : '2'}
          </div>
          <span className="font-medium">Components</span>
        </div>
        <div className="w-16 h-px bg-border"></div>
        <div className={`flex items-center gap-2 ${step >= 3 ? 'text-primary' : 'text-muted-foreground'}`}>
          <div className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold ${step >= 3 ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
            3
          </div>
          <span className="font-medium">Setup</span>
        </div>
      </div>

      {/* Step 1: User Goal (Page Type) */}
      {step === 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">What is the user trying to accomplish?</CardTitle>
            <CardDescription className="text-base">
              Select the primary user objective for this page
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {PAGE_TYPES.map(type => (
                <Card
                  key={type.value}
                  className={`cursor-pointer transition-all hover:shadow-md ${
                    pageType === type.value
                      ? 'border-primary ring-2 ring-primary shadow-md'
                      : 'hover:border-primary/50'
                  }`}
                  onClick={() => setPageType(type.value)}
                >
                  <CardHeader className="space-y-3">
                    <CardTitle className="text-lg">{type.label}</CardTitle>
                    <CardDescription className="text-sm whitespace-pre-line leading-relaxed">
                      {type.description}
                    </CardDescription>
                  </CardHeader>
                </Card>
              ))}
            </div>

            <div className="flex justify-end gap-3 pt-6">
              <Button onClick={() => navigate('/manual-testing/sessions')} variant="outline" size="lg">
                Cancel
              </Button>
              <Button onClick={() => setStep(2)} disabled={!pageType} size="lg">
                Next: Select Components →
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 2: Components */}
      {step === 2 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Select Interactive Components</CardTitle>
            <CardDescription className="text-base">
              Choose which components are present on this page
              {detectedComponents.length > 0 && (
                <span className="block mt-2 text-primary font-medium">
                  ✓ {detectedComponents.length} components auto-detected from scan
                </span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {COMPONENT_GROUPS.map(group => (
              <div key={group.title} className="space-y-3">
                <div className="flex items-start gap-3">
                  <Checkbox
                    id={`group-${group.title}`}
                    checked={group.components.length > 0 && group.components.every(c => selectedComponents.includes(c.value))}
                    onCheckedChange={(checked) => {
                      if (checked) {
                        setSelectedComponents(prev => [
                          ...prev,
                          ...group.components.map(c => c.value).filter(v => !prev.includes(v))
                        ]);
                      } else {
                        setSelectedComponents(prev =>
                          prev.filter(v => !group.components.find(c => c.value === v))
                        );
                      }
                    }}
                    disabled={group.components.length === 0}
                  />
                  <div className="flex-1">
                    <Label
                      htmlFor={`group-${group.title}`}
                      className="text-base font-semibold cursor-pointer"
                    >
                      {group.title}
                    </Label>
                    <p className="text-sm text-muted-foreground mt-1">
                      {group.description}
                    </p>
                    
                    {group.components.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-3">
                        {group.components.map(component => (
                          <Badge
                            key={component.value}
                            variant={selectedComponents.includes(component.value) ? "default" : "outline"}
                            className="cursor-pointer px-3 py-1 text-sm"
                            onClick={() => toggleComponent(component.value)}
                          >
                            {component.label}
                            {detectedComponents.includes(component.value) && (
                              <span className="ml-1">✓</span>
                            )}
                          </Badge>
                        ))}
                      </div>
                    )}
                    
                    {group.components.length === 0 && (
                      <p className="text-sm text-muted-foreground italic mt-2">
                        Tests included in base checklist
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}

            <div className="flex justify-between pt-6">
              <Button onClick={() => setStep(1)} variant="outline" size="lg">
                ← Back
              </Button>
              <Button onClick={() => setStep(3)} size="lg">
                Next: Setup Session →
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3: Tester Details */}
      {step === 3 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-2xl">Setup Testing Session</CardTitle>
            <CardDescription className="text-base">
              Review your selections and enter tester information
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Preview Summary */}
            <div className="bg-primary/5 border-2 border-primary/20 p-6 rounded-lg space-y-4">
              <h4 className="font-semibold text-lg">Session Configuration</h4>
              
              <div className="space-y-3">
                <div>
                  <span className="font-medium text-sm text-muted-foreground">User Goal:</span>
                  <p className="text-base mt-1">
                    {PAGE_TYPES.find(t => t.value === pageType)?.label}
                  </p>
                </div>
                
                <div>
                  <span className="font-medium text-sm text-muted-foreground">Selected Components:</span>
                  {selectedComponents.length > 0 ? (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {selectedComponents.map(c => {
                        const component = COMPONENT_GROUPS.flatMap(g => g.components).find(comp => comp.value === c);
                        return component ? (
                          <Badge key={c} variant="secondary" className="text-sm">
                            {component.label}
                          </Badge>
                        ) : null;
                      })}
                    </div>
                  ) : (
                    <p className="text-base mt-1 text-muted-foreground italic">
                      No additional components selected
                    </p>
                  )}
                </div>

                <div>
                  <span className="font-medium text-sm text-muted-foreground">Estimated Tests:</span>
                  <p className="text-base mt-1">
                    ~{15 + selectedComponents.length * 3} checklist items
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="tester-name" className="text-base font-medium">
                Tester Name *
              </Label>
              <Input
                id="tester-name"
                placeholder="Enter your full name"
                value={testerName}
                onChange={e => setTesterName(e.target.value)}
                className="text-base"
              />
              <p className="text-sm text-muted-foreground">
                Your name will be recorded with the test results
              </p>
            </div>

            <div className="flex justify-between pt-6">
              <Button onClick={() => setStep(2)} variant="outline" disabled={isGenerating} size="lg">
                ← Back
              </Button>
              <Button 
                onClick={handleGenerate} 
                disabled={!testerName || isGenerating} 
                size="lg"
                className="min-w-[200px]"
              >
                {isGenerating ? 'Generating Checklist...' : 'Start Testing Session'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
