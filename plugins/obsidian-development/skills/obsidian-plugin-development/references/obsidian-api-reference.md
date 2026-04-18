# Obsidian TypeScript API - Quick Reference

Source: `node_modules/obsidian/obsidian.d.ts`

## Plugin (extends Component)

```typescript
onload(): Promise<void> | void
onunload(): void
addCommand(command: Command): Command
addSettingTab(settingTab: PluginSettingTab): void
addRibbonIcon(icon: IconName, title: string, callback: (evt: MouseEvent) => any): HTMLElement
addStatusBarItem(): HTMLElement              // Desktop only
registerView(type: string, viewCreator: ViewCreator): void
registerExtensions(extensions: string[], viewType: string): void
registerMarkdownPostProcessor(postProcessor: MarkdownPostProcessor, sortOrder?: number): MarkdownPostProcessor
registerMarkdownCodeBlockProcessor(language: string, handler: (source, el, ctx) => Promise<void> | void, sortOrder?: number): MarkdownPostProcessor
registerEditorExtension(extension: Extension): void
registerEditorSuggest(editorSuggest: EditorSuggest<any>): void
registerObsidianProtocolHandler(action: string, handler: ObsidianProtocolHandler): void
loadData(): Promise<any>
saveData(data: any): Promise<void>
manifest: PluginManifest
app: App
```

## App

```typescript
vault: Vault
workspace: Workspace
metadataCache: MetadataCache
fileManager: FileManager
keymap: Keymap
scope: Scope
isDarkMode(): boolean
loadLocalStorage(key: string): any | null
saveLocalStorage(key: string, data: unknown | null): void
```

## Vault (extends Events)

```typescript
// Properties
adapter: DataAdapter
configDir: string                            // Usually '.obsidian'

// Retrieval
getName(): string
getAbstractFileByPath(path: string): TAbstractFile | null
getFileByPath(path: string): TFile | null
getFolderByPath(path: string): TFolder | null
getRoot(): TFolder
getAllLoadedFiles(): TAbstractFile[]
getAllFolders(includeRoot?: boolean): TFolder[]
getMarkdownFiles(): TFile[]
getFiles(): TFile[]

// Operations
create(path: string, data: string, options?: DataWriteOptions): Promise<TFile>
createBinary(path: string, data: ArrayBuffer, options?: DataWriteOptions): Promise<TFile>
createFolder(path: string): Promise<TFolder>
read(file: TFile): Promise<string>
cachedRead(file: TFile): Promise<string>
readBinary(file: TFile): Promise<ArrayBuffer>
modify(file: TFile, data: string, options?: DataWriteOptions): Promise<void>
modifyBinary(file: TFile, data: ArrayBuffer, options?: DataWriteOptions): Promise<void>
append(file: TFile, data: string, options?: DataWriteOptions): Promise<void>
process(file: TFile, fn: (data: string) => string, options?: DataWriteOptions): Promise<string>
copy<T extends TAbstractFile>(file: T, newPath: string): Promise<T>
delete(file: TAbstractFile, force?: boolean): Promise<void>
trash(file: TAbstractFile, system: boolean): Promise<void>
rename(file: TAbstractFile, newPath: string): Promise<void>
getResourcePath(file: TFile): string

// Events
on('create', callback: (file: TAbstractFile) => any): EventRef
on('delete', callback: (file: TAbstractFile) => any): EventRef
on('rename', callback: (file: TAbstractFile, oldPath: string) => any): EventRef
on('modify', callback: (file: TAbstractFile) => any): EventRef

static recurseChildren(root: TFolder, cb: (file: TAbstractFile) => any): void
```

## Workspace (extends Events)

```typescript
// Properties
containerEl: HTMLElement
layoutReady: boolean
activeEditor: MarkdownFileInfo | null

// Leaf management
getLeaf(newLeaf?: 'split' | true | 'tab' | 'window' | false): WorkspaceLeaf
getLeavesOfType(viewType: string): WorkspaceLeaf[]
getMostRecentLeaf(root?: WorkspaceParent): WorkspaceLeaf | null
getLeftLeaf(split: boolean): WorkspaceLeaf | null
getRightLeaf(split: boolean): WorkspaceLeaf | null
ensureSideLeaf(type: string, side: Side, options?: {active?, split?, reveal?, state?}): Promise<WorkspaceLeaf>
setActiveLeaf(leaf: WorkspaceLeaf, params?: {focus?: boolean}): void
createLeafBySplit(leaf: WorkspaceLeaf, direction?: SplitDirection, before?: boolean): WorkspaceLeaf

// File/View access
getActiveFile(): TFile | null
getActiveViewOfType<T extends View>(type: Constructor<T>): T | null
openLinkText(linktext: string, sourcePath: string, newLeaf?: PaneType | boolean, openViewState?: OpenViewState): Promise<void>

// Layout
onLayoutReady(callback: () => any): void
iterateRootLeaves(callback: (leaf: WorkspaceLeaf) => any): void
iterateAllLeaves(callback: (leaf: WorkspaceLeaf) => any): void
requestSaveLayout: Debouncer<[], Promise<void>>

// Events
on('active-leaf-change', callback: (leaf: WorkspaceLeaf | null) => any): EventRef
on('file-open', callback: (file: TFile | null) => any): EventRef
on('layout-change', callback: () => any): EventRef
on('css-change', callback: () => any): EventRef
on('file-menu', callback: (menu: Menu, file: TAbstractFile, source: string, leaf?: WorkspaceLeaf) => any): EventRef
on('editor-menu', callback: (menu: Menu, editor: Editor, info: MarkdownView | MarkdownFileInfo) => any): EventRef
```

## MetadataCache (extends Events)

```typescript
getFileCache(file: TFile): CachedMetadata | null
getCache(path: string): CachedMetadata | null
getFirstLinkpathDest(linkpath: string, sourcePath: string): TFile | null
fileToLinktext(file: TFile, sourcePath: string, omitMdExtension?: boolean): string
resolvedLinks: Record<string, Record<string, number>>
unresolvedLinks: Record<string, Record<string, number>>

// Events
on('changed', callback: (file: TFile, data: string, cache: CachedMetadata) => any): EventRef
on('deleted', callback: (file: TFile, prevCache: CachedMetadata | null) => any): EventRef
on('resolve', callback: (file: TFile) => any): EventRef
on('resolved', callback: () => any): EventRef
```

## FileManager

```typescript
renameFile(file: TAbstractFile, newPath: string): Promise<void>
trashFile(file: TAbstractFile): Promise<void>
promptForDeletion(file: TAbstractFile): Promise<boolean>
generateMarkdownLink(file: TFile, sourcePath: string, subpath?: string, alias?: string): string
processFrontMatter(file: TFile, fn: (frontmatter: any) => void, options?: DataWriteOptions): Promise<void>
getAvailablePathForAttachment(filename: string, sourcePath?: string): Promise<string>
getNewFileParent(sourcePath: string, newFilePath?: string): TFolder
```

## Component

```typescript
onload(): void
onunload(): void
load(): void
unload(): void
addChild<T extends Component>(component: T): T
removeChild<T extends Component>(component: T): T
register(cb: () => any): void
registerEvent(eventRef: EventRef): void
registerDomEvent<K extends keyof HTMLElementEventMap>(el: HTMLElement, type: K, callback: (ev: HTMLElementEventMap[K]) => any, options?: boolean | AddEventListenerOptions): void
registerInterval(id: number): number
```

## View (extends Component)

```typescript
app: App
icon: IconName
leaf: WorkspaceLeaf
containerEl: HTMLElement
navigation: boolean

onOpen(): Promise<void>
onClose(): Promise<void>
getViewType(): string                        // Abstract
getDisplayText(): string                     // Abstract
getIcon(): IconName
getState(): Record<string, unknown>
setState(state: unknown, result: ViewStateResult): Promise<void>
onResize(): void
onPaneMenu(menu: Menu, source: string): void
```

## ItemView (extends View)

```typescript
contentEl: HTMLElement
constructor(leaf: WorkspaceLeaf)
addAction(icon: IconName, title: string, callback: (evt: MouseEvent) => any): HTMLElement
```

## Modal

```typescript
app: App
scope: Scope
containerEl: HTMLElement
modalEl: HTMLElement
titleEl: HTMLElement
contentEl: HTMLElement

constructor(app: App)
onOpen(): Promise<void> | void
onClose(): void
open(): void
close(): void
setTitle(title: string): this
setContent(content: string | DocumentFragment): this
```

## SuggestModal<T> (extends Modal)

```typescript
inputEl: HTMLInputElement
resultContainerEl: HTMLElement
limit: number
emptyStateText: string

setPlaceholder(placeholder: string): void
setInstructions(instructions: Instruction[]): void

// Abstract -- implement in subclass
getSuggestions(query: string): T[] | Promise<T[]>
renderSuggestion(value: T, el: HTMLElement): void
onChooseSuggestion(item: T, evt: MouseEvent | KeyboardEvent): void
```

## AbstractInputSuggest<T>

```typescript
limit: number                                // Default 100, 0 to disable
constructor(app: App, textInputEl: HTMLInputElement | HTMLDivElement)
setValue(value: string): void
getValue(): string

// Abstract
protected getSuggestions(query: string): T[] | Promise<T[]>
onSuggestion(callback: (value: T, evt: MouseEvent | KeyboardEvent) => void): void
```

## Setting

```typescript
settingEl: HTMLElement
infoEl: HTMLElement
nameEl: HTMLElement
descEl: HTMLElement
controlEl: HTMLElement

constructor(containerEl: HTMLElement)
setName(name: string | DocumentFragment): this
setDesc(desc: string | DocumentFragment): this
setClass(cls: string): this
setHeading(): this
setDisabled(disabled: boolean): this
setTooltip(tooltip: string, options?: TooltipOptions): this

addButton(cb: (c: ButtonComponent) => any): this
addExtraButton(cb: (c: ExtraButtonComponent) => any): this
addToggle(cb: (c: ToggleComponent) => any): this
addText(cb: (c: TextComponent) => any): this
addSearch(cb: (c: SearchComponent) => any): this
addTextArea(cb: (c: TextAreaComponent) => any): this
addSlider(cb: (c: SliderComponent) => any): this
addDropdown(cb: (c: DropdownComponent) => any): this
addColorPicker(cb: (c: ColorComponent) => any): this
addMomentFormat(cb: (c: MomentFormatComponent) => any): this
addProgressBar(cb: (c: ProgressBarComponent) => any): this
then(cb: (setting: this) => any): this
clear(): this
```

## Menu & MenuItem

```typescript
// Menu
addItem(cb: (item: MenuItem) => any): this
addSeparator(): this
showAtMouseEvent(evt: MouseEvent): this
showAtPosition(position: MenuPositionDef, doc?: Document): this
hide(): this
close(): void
static forEvent(evt: PointerEvent | MouseEvent): Menu

// MenuItem
setTitle(title: string | DocumentFragment): this
setIcon(icon: IconName | null): this
setChecked(checked: boolean | null): this
setDisabled(disabled: boolean): this
setWarning(isWarning: boolean): this
onClick(callback: (evt: MouseEvent | KeyboardEvent) => any): this
setSection(section: string): this
```

## Notice

```typescript
constructor(message: string | DocumentFragment, duration?: number)
setMessage(message: string | DocumentFragment): this
hide(): void
```

## WorkspaceLeaf

```typescript
view: View
parent: WorkspaceTabs | WorkspaceMobileDrawer
openFile(file: TFile, openState?: OpenViewState): Promise<void>
open(view: View): Promise<View>
getViewState(): ViewState
setViewState(state: ViewState, result?: ViewStateResult): Promise<void>
```

## TAbstractFile / TFile / TFolder

```typescript
// TAbstractFile
vault: Vault
path: string
name: string
parent: TFolder | null

// TFile
stat: FileStats                              // { ctime, mtime, size }
basename: string
extension: string

// TFolder
children: TAbstractFile[]
isRoot(): boolean
```

## MarkdownRenderer

```typescript
static render(app: App, markdown: string, el: HTMLElement, sourcePath: string, component: Component): Promise<void>
```

## Platform

```typescript
isDesktop: boolean
isMobile: boolean
isDesktopApp: boolean
isMobileApp: boolean
isIosApp: boolean
isAndroidApp: boolean
isPhone: boolean
isTablet: boolean
isMacOS: boolean
isWin: boolean
isLinux: boolean
isSafari: boolean
```

## Helper Functions

```typescript
// DOM creation
createEl<K>(tag: K, o?: DomElementInfo | string): HTMLElementTagNameMap[K]
createDiv(o?: DomElementInfo | string): HTMLDivElement
createSpan(o?: DomElementInfo | string): HTMLSpanElement
createFragment(callback?: (el: DocumentFragment) => void): DocumentFragment

// HTML sanitization
sanitizeHTMLToDom(html: string): DocumentFragment

// File utilities
normalizePath(path: string): string

// Icons
addIcon(iconId: string, svgContent: string): void
getIcon(iconId: string): SVGSVGElement | null
getIconIds(): IconName[]

// Network
requestUrl(request: RequestUrlParam | string): RequestUrlResponsePromise

// Date/time
const moment: typeof Moment

// Version
requireApiVersion(version: string): boolean
```

## HTMLElement Extensions

```typescript
// Text
getText(): string
setText(val: string | DocumentFragment): void

// Attributes
setAttr(name: string, value: string | number | boolean | null): void
setAttrs(obj: Record<string, string | number | boolean | null>): void
getAttr(name: string): string | null

// Classes
addClass(...classes: string[]): void
addClasses(classes: string[]): void
removeClass(...classes: string[]): void
removeClasses(classes: string[]): void
toggleClass(classes: string | string[], value: boolean): void
hasClass(cls: string): boolean

// Visibility
show(): void
hide(): void
toggle(show: boolean): void
toggleVisibility(visible: boolean): void

// CSS
setCssStyles(styles: Partial<CSSStyleDeclaration>): void
setCssProps(props: Record<string, string>): void
getCssPropertyValue(property: string, pseudoElement?: string): string

// DOM creation (on existing elements)
createEl<K>(tag: K, o?: DomElementInfo | string): HTMLElementTagNameMap[K]
createDiv(o?: DomElementInfo | string): HTMLDivElement
createSpan(o?: DomElementInfo | string): HTMLSpanElement
createSvg<K>(tag: K, o?: SvgElementInfo | string): SVGElementTagNameMap[K]

// Traversal
matchParent(selector: string, lastParent?: Element): Element | null
isActiveElement(): boolean
```

## DomElementInfo

```typescript
interface DomElementInfo {
  cls?: string | string[];
  text?: string | DocumentFragment;
  attr?: Record<string, string | number | boolean | null>;
  title?: string;
  parent?: Node;
  value?: string;
  type?: string;
  prepend?: boolean;
  placeholder?: string;
  href?: string;
}
```

## CachedMetadata

```typescript
interface CachedMetadata {
  links?: LinkCache[];
  embeds?: EmbedCache[];
  tags?: TagCache[];
  headings?: HeadingCache[];
  sections?: SectionCache[];
  listItems?: ListItemCache[];
  frontmatter?: FrontMatterCache;
  frontmatterLinks?: FrontmatterLinkCache[];
  frontmatterPosition?: Pos;
  blocks?: Record<string, BlockCache>;
}
```

## Command

```typescript
interface Command {
  id: string;
  name: string;
  icon?: IconName;
  mobileOnly?: boolean;
  repeatable?: boolean;
  callback?: () => any;
  checkCallback?: (checking: boolean) => boolean | void;
  editorCallback?: (editor: Editor, ctx: MarkdownView | MarkdownFileInfo) => any;
  editorCheckCallback?: (checking: boolean, editor: Editor, ctx: MarkdownView | MarkdownFileInfo) => boolean | void;
  hotkeys?: Hotkey[];
}
```
