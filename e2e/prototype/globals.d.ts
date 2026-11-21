// Existing vanilla-JS Workbench globals inspected inside Playwright's browser context.
declare let state: any;
declare let projectEpoch: number;
declare let uploadTarget: string;
declare let aiStatus: any;
declare const STEPS: any[];
declare const NAV: any[];
declare function blankState(): any;
declare function render(): void;
declare function go(page: string): void;
declare function workflowStates(): string[];
declare function stepStates(): string[];
declare function closeCompletion(): void;
declare function handleStepCompletion(title: string, target: string, epoch: number): void;
declare function runAITopic(): Promise<void>;
interface Window { workbenchReady: Promise<void>; }
