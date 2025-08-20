import React, { useState } from "react";
import { Button } from "~/components/ui/button";
import { Input } from "~/components/ui/input";
import { Label } from "~/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "~/components/ui/card";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "~/components/ui/dropdown-menu";
import { Plus, X, ChevronDown } from "lucide-react";
import { type PreviewContent } from "~/video-compositions/StandalonePreview";
import { generateUUID } from "~/utils/uuid";

interface StandalonePreviewControlsProps {
  previewContent: PreviewContent[];
  onAddContent: (content: PreviewContent) => void;
  onRemoveContent: (id: string) => void;
  onUpdateContent: (id: string, updates: Partial<PreviewContent>) => void;
  onClearContent: () => void;
}

export function StandalonePreviewControls({
  previewContent,
  onAddContent,
  onRemoveContent,
  onUpdateContent,
  onClearContent,
}: StandalonePreviewControlsProps) {
  const [newContentType, setNewContentType] = useState<"text" | "image" | "video" | "audio">("text");
  const [isExpanded, setIsExpanded] = useState(false);

  const handleAddContent = () => {
    const baseContent: PreviewContent = {
      id: generateUUID(),
      type: newContentType,
      position: {
        x: Math.random() * 200,
        y: Math.random() * 200,
        width: 400,
        height: 200,
      },
      duration: 5,
    };

    if (newContentType === "text") {
      baseContent.text = {
        content: "New Text Element",
        fontSize: 48,
        color: "#ffffff",
        fontFamily: "Arial, sans-serif",
        textAlign: "center",
        fontWeight: "normal",
      };
    } else {
      baseContent.src = ""; // User will need to set this
    }

    onAddContent(baseContent);
  };

  if (!isExpanded) {
    return (
      <Button
        variant="outline"
        size="sm"
        onClick={() => setIsExpanded(true)}
        className="text-xs h-6"
      >
        <Plus className="h-3 w-3 mr-1" />
        Preview Controls
      </Button>
    );
  }

  return (
    <Card className="w-80 bg-background/95 backdrop-blur">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm">Standalone Preview Controls</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsExpanded(false)}
            className="h-6 w-6 p-0"
          >
            <X className="h-3 w-3" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Add new content */}
        <div className="space-y-2">
          <Label className="text-xs">Add Content</Label>
          <div className="flex gap-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" className="h-6 text-xs capitalize">
                  {newContentType} <ChevronDown className="h-3 w-3 ml-1" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setNewContentType("text")}>
                  Text
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setNewContentType("image")}>
                  Image
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setNewContentType("video")}>
                  Video
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setNewContentType("audio")}>
                  Audio
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
            <Button size="sm" onClick={handleAddContent} className="h-6 px-2 text-xs">
              <Plus className="h-3 w-3" />
            </Button>
          </div>
        </div>

        {/* Content list */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs">Content ({previewContent.length})</Label>
            <Button
              variant="outline"
              size="sm"
              onClick={onClearContent}
              className="h-5 px-2 text-xs"
            >
              Clear All
            </Button>
          </div>
          
          <div className="max-h-40 overflow-y-auto space-y-1">
            {previewContent.map((content) => (
              <div key={content.id} className="flex items-center justify-between bg-muted/50 p-2 rounded text-xs">
                <div className="flex-1">
                  <div className="font-medium">
                    {content.type} - {content.type === "text" ? content.text?.content : content.src || "No source"}
                  </div>
                  <div className="text-muted-foreground">
                    {content.position.width}×{content.position.height} @ ({content.position.x}, {content.position.y})
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => onRemoveContent(content.id)}
                  className="h-5 w-5 p-0 text-muted-foreground hover:text-destructive"
                >
                  <X className="h-3 w-3" />
                </Button>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
