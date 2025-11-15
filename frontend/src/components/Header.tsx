import { useState } from "react";
import { Settings } from "lucide-react";
import { Button } from "./ui/button";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "./ui/dialog";
import { Input } from "./ui/input";
import { PANE_LABELS } from "../lib/utils";

interface DeploymentConfig {
  name: string;
  repo: string;
  deploymentUrl: string;
}

export function Header() {
  const [open, setOpen] = useState(false);

  // Generate default configurations for each pane
  const [configs, setConfigs] = useState<DeploymentConfig[]>(
    PANE_LABELS.map((label, index) => ({
      name: label,
      repo: "git@github.com:danny-hunt/example-hackernews.git",
      deploymentUrl: `http://localhost:300${index + 1}`,
    }))
  );

  const handleConfigChange = (index: number, field: keyof DeploymentConfig, value: string) => {
    setConfigs((prev) => {
      const newConfigs = [...prev];
      newConfigs[index] = { ...newConfigs[index], [field]: value };
      return newConfigs;
    });
  };

  return (
    <div className="border-b bg-background">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">Visual Vibing</h1>
          <span className="text-sm text-muted-foreground">an orchestration layer designed for vibe coding</span>
        </div>

        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button variant="ghost" size="icon">
              <Settings className="h-5 w-5" />
            </Button>
          </DialogTrigger>

          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>Configuration</DialogTitle>
              <DialogDescription>Configure deployment settings for each pane</DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              {configs.map((config, index) => (
                <div key={index} className="border rounded-lg p-4 space-y-3">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Name</label>
                    <Input
                      value={config.name}
                      onChange={(e) => handleConfigChange(index, "name", e.target.value)}
                      placeholder="Deployment name"
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-1 block">Repository URL</label>
                    <Input
                      value={config.repo}
                      onChange={(e) => handleConfigChange(index, "repo", e.target.value)}
                      placeholder="git@github.com:user/repo.git"
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium mb-1 block">Deployment URL</label>
                    <Input
                      value={config.deploymentUrl}
                      onChange={(e) => handleConfigChange(index, "deploymentUrl", e.target.value)}
                      placeholder="http://localhost:3000"
                    />
                  </div>
                </div>
              ))}
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
}
