# Claude Design Prompt: AIScope - AI Visibility Tracking Platform

## Project Overview

Design a complete multi-tenant SaaS analytics dashboard called **AIScope** that tracks how brands appear across AI answer engines (ChatGPT, Perplexity, Gemini, Google AI Overviews, Copilot). Users set up projects for their brand, add prompts their customers would ask AI chatbots, and the system runs those prompts daily to measure brand visibility, position, sentiment, and which sources the AI cites. Think of it as "Google Search Console but for AI answers."

The platform serves marketing teams and agencies managing 5 to 20 client brands. The core value: showing clients exactly where they appear (or don't appear) when people ask AI chatbots questions in their niche.

## Design System

Use the attached Clay design system (DESIGN-clay.md) as the visual foundation, but **adapt it for a data-dense analytics dashboard context**. Key adaptations:

- Keep the warm cream canvas (`#fffaf0`) as the app background, it differentiates us from every dark-mode or cool-gray analytics tool
- Keep Inter as the primary font family throughout (we don't have Plain Black license)
- Use the Clay color palette but repurpose the brand colors as **data visualization colors** and **platform identity colors**: brand-pink for ChatGPT data, brand-teal for Perplexity, brand-lavender for Gemini, brand-ochre for Google AI Overviews, brand-coral for Copilot
- Keep the rounded corners system (rounded-md for inputs/buttons, rounded-lg for cards, rounded-xl for feature panels)
- Keep the warm cream surfaces for cards (`surface-card`, `surface-soft`) instead of the typical white-on-gray dashboard look
- Use the hairline borders for card edges, no heavy shadows
- The saturated color cards become **metric highlight cards** on the dashboard (e.g. visibility % on a teal card, sentiment on a lavender card)
- Use success/warning/error colors for sentiment indicators (green = positive, yellow = neutral, red = negative)
- NO claymation illustrations or 3D mascots, replace those with clean data visualizations and simple iconography (Lucide icons)

The overall vibe should feel like: "warm, premium analytics" rather than "cold enterprise dashboard." Think Linear meets Notion in warmth, but with Clay's cream palette.

## Tech Stack for Implementation

- **React 18+** with JSX (not TypeScript for now)
- **React Router v6** for routing
- **Tailwind CSS** for styling (map the Clay design tokens to Tailwind config)
- **Recharts** for all charts and data visualizations
- **Lucide React** for icons
- **TanStack Query (React Query)** for API data fetching and caching
- **Zustand** for lightweight global state (auth, active project)
- **React Hook Form + Zod** for form validation
- No component library (build custom components matching the Clay design system)

## Complete Folder Structure

```
frontend/
  src/
    main.jsx                          # Entry point, renders App
    App.jsx                           # Router setup, auth provider, query provider
    index.css                         # Tailwind directives + Clay CSS custom properties

    config/
      api.js                          # Axios instance with base URL, auth interceptor
      routes.js                       # Route path constants
      platforms.js                    # Platform metadata (name, color, icon mapping)
      queryKeys.js                    # TanStack Query key factory

    store/
      authStore.js                    # Zustand: user, token, org, login/logout
      projectStore.js                 # Zustand: active project, project list

    hooks/
      useAuth.js                      # Auth state + guard logic
      useProjects.js                  # TanStack Query hooks for projects CRUD
      useBrands.js                    # TanStack Query hooks for brands CRUD
      usePrompts.js                   # TanStack Query hooks for prompts CRUD
      useTrackingConfigs.js           # TanStack Query hooks for tracking configs
      useMetrics.js                   # TanStack Query hooks for dashboard metrics
      useSourceMetrics.js             # TanStack Query hooks for source analytics
      useScrapeRuns.js                # TanStack Query hooks for scrape run history

    lib/
      components/
        ui/                           # Atomic design system components
          Button.jsx                  # Primary, secondary, text-link, on-color variants
          Input.jsx                   # Text input with label, error state, focus ring
          Select.jsx                  # Dropdown select matching input style
          Badge.jsx                   # Pill badges (status, platform, source type)
          Card.jsx                    # Base card (cream surface, hairline border, rounded-lg)
          MetricCard.jsx              # Colored metric card (visibility, sentiment, etc.)
          Modal.jsx                   # Overlay dialog with backdrop
          Dropdown.jsx                # Action dropdown menu
          Table.jsx                   # Data table with sorting, pagination
          Tabs.jsx                    # Pill-shaped tab navigation (Clay category-tab style)
          EmptyState.jsx              # Illustration + message for no-data states
          LoadingSpinner.jsx          # Skeleton/spinner states
          Toast.jsx                   # Notification toasts (success, error, info)
          Avatar.jsx                  # User/org avatar circle
          Tooltip.jsx                 # Hover tooltip

        charts/                       # Recharts wrapper components
          VisibilityChart.jsx         # Area/line chart: visibility % over time per platform
          PositionChart.jsx           # Line chart: average position over time
          SentimentChart.jsx          # Line chart: sentiment score over time
          ShareOfVoiceChart.jsx       # Stacked bar or donut: brand share comparison
          SourceBreakdownChart.jsx    # Horizontal bar: top cited domains
          SourceTypeChart.jsx         # Donut: citation distribution by type (Reddit, review sites, editorial, etc.)
          PlatformComparisonChart.jsx # Grouped bar: visibility across platforms side by side
          TrendSparkline.jsx          # Tiny inline sparkline for table cells

        layout/
          AppShell.jsx                # Main app frame: sidebar + topbar + content area
          Sidebar.jsx                 # Left sidebar: logo, nav links, project switcher, user menu
          Topbar.jsx                  # Top bar: breadcrumbs, date range picker, search
          ProjectSwitcher.jsx         # Dropdown to switch active project
          DateRangePicker.jsx         # Date range selector (7d, 30d, 90d, custom)
          PageHeader.jsx              # Page title + subtitle + action buttons area

        features/
          projects/
            ProjectCard.jsx           # Project summary card for the projects list
            ProjectForm.jsx           # Create/edit project form (name, website URL)
            ProjectSetupWizard.jsx    # Step-by-step onboarding: create project > add brands > add prompts > configure tracking

          brands/
            BrandCard.jsx             # Brand/competitor card with visibility spark
            BrandForm.jsx             # Create/edit brand (name, aliases, is_primary toggle)
            CompetitorList.jsx        # List of competitor brands with quick-add

          prompts/
            PromptCard.jsx            # Prompt with latest visibility per platform
            PromptForm.jsx            # Create/edit prompt with topic/tag assignment
            PromptTable.jsx           # Full table view: prompt text, topic, tags, visibility per platform, status
            PromptResultModal.jsx     # Modal showing full captured AI answer for a prompt
            TagManager.jsx            # Inline tag add/remove chips

          tracking/
            TrackingConfigForm.jsx    # Select platforms + countries + frequency for prompts
            PlatformSelector.jsx      # Multi-select platforms with colored platform badges
            CountrySelector.jsx       # Multi-select countries

          dashboard/
            OverviewMetrics.jsx       # Row of 4 MetricCards: visibility, avg position, avg sentiment, share of voice
            VisibilityTrend.jsx       # Main visibility over time chart with platform breakdown
            TopCompetitors.jsx        # Competitor comparison table with sparklines
            TopSources.jsx            # Top cited domains card
            RecentActivity.jsx        # Latest scrape runs and status indicators
            PlatformBreakdown.jsx     # Per-platform visibility summary cards

          sources/
            SourceTable.jsx           # Full table: domain, citation count, source type, trend
            SourceTypeFilter.jsx      # Filter by source type (review, reddit, editorial, etc.)
            SourceDetail.jsx          # Expanded view: all URLs from a domain, which prompts cited it

          competitors/
            CompetitorOverview.jsx    # Side-by-side visibility/position/sentiment comparison
            CompetitorMatrix.jsx      # Matrix: brands (rows) x prompts (columns), cells show mentioned/not
            GapAnalysis.jsx           # Prompts where competitors appear but you don't

          scrape/
            RunHistory.jsx            # Table of recent scrape runs with status badges
            RunDetail.jsx             # View raw captured answer, screenshot, parsed data
            ManualRunButton.jsx       # Trigger a manual scrape for testing

    pages/
      auth/
        LoginPage.jsx                 # Email + password login
        SignupPage.jsx                # Signup with org name
        VerifyEmailPage.jsx           # Email verification
        ForgotPasswordPage.jsx        # Password reset request
        ResetPasswordPage.jsx         # Password reset form

      onboarding/
        OnboardingPage.jsx            # Post-signup project setup wizard (wraps ProjectSetupWizard)

      app/
        DashboardPage.jsx             # Main dashboard: overview metrics + charts + competitor summary + sources
        PromptsPage.jsx               # Prompt management: table + CRUD + results
        SourcesPage.jsx               # Source analytics: citation domains + types + trends
        CompetitorsPage.jsx           # Competitor comparison: matrix + gap analysis + charts
        ProjectSettingsPage.jsx       # Project settings: edit project, manage brands, tracking configs
        BrandsPage.jsx                # Brand/competitor management within a project
        TrackingPage.jsx              # Tracking configuration: platforms, countries, frequency
        RunHistoryPage.jsx            # Scrape run history and debugging
        AccountSettingsPage.jsx       # User profile, password change
        OrgSettingsPage.jsx           # Organization settings, member management (admin only)

    utils/
      formatters.js                   # Number formatting (percentages, positions), date formatting
      platformColors.js               # Map platform IDs to Clay brand colors
      sourceTypeLabels.js             # Human-readable source type labels + colors
```

## Routing Structure

```
/login                              # LoginPage (public)
/signup                             # SignupPage (public)
/verify-email                       # VerifyEmailPage (public)
/forgot-password                    # ForgotPasswordPage (public)
/reset-password                     # ResetPasswordPage (public)

/onboarding                         # OnboardingPage (protected, post-signup)

/dashboard                          # DashboardPage (protected, default after login)
/prompts                            # PromptsPage (protected)
/sources                            # SourcesPage (protected)
/competitors                        # CompetitorsPage (protected)
/runs                               # RunHistoryPage (protected)

/settings/project                   # ProjectSettingsPage (protected)
/settings/brands                    # BrandsPage (protected)
/settings/tracking                  # TrackingPage (protected)
/settings/account                   # AccountSettingsPage (protected)
/settings/organization              # OrgSettingsPage (protected, admin only)
```

Use a `ProtectedRoute` wrapper that checks auth state and redirects to `/login` if not authenticated. Use `AppShell` as the layout wrapper for all `/dashboard`, `/prompts`, `/sources`, `/competitors`, `/runs`, and `/settings/*` routes so they share the sidebar + topbar.

## Screen-by-Screen Design Specifications

### 1. Login Page
Clean centered card on cream canvas. Logo at top center. Email + password inputs (Clay `text-input` style). "Sign in" primary button full width. "Forgot password?" text-link below. "Don't have an account? Sign up" text-link at bottom. No sidebar or nav, just the form card.

### 2. Signup Page
Same layout as login. Fields: user name, email, organization name, password, confirm password. "Create account" primary button. "Already have an account? Sign in" text-link.

### 3. Onboarding Wizard (post-signup, 4 steps)
Full-page wizard with a horizontal step indicator at top. Steps:

**Step 1: Create Project** -- "What brand do you want to track?" Name input + website URL input.

**Step 2: Add Your Brand** -- Brand name + aliases (comma-separated or chip input). Explain: "We'll look for these names in AI answers."

**Step 3: Add Competitors** -- "Who are you competing against in AI answers?" Simple repeatable input to add 3-5 competitor brand names. Show them as removable chips/cards.

**Step 4: Configure Tracking** -- Platform multi-select (ChatGPT, Perplexity, Gemini, AI Overviews, Copilot) with colored badges. Country selector (start with US pre-selected). Frequency toggle (Daily recommended). "Start Tracking" primary button.

After completion, redirect to dashboard with an empty state prompting them to add their first prompts.

### 4. App Shell (layout for all authenticated pages)
**Sidebar (left, 240px wide, collapsible to 64px icons-only):**
- Top: AIScope logo/wordmark
- Project switcher dropdown (shows current project name, click to switch or create new)
- Navigation links with Lucide icons:
  - Dashboard (LayoutDashboard icon)
  - Prompts (MessageSquare icon)
  - Sources (Link icon)
  - Competitors (Users icon)
  - Run History (History icon)
  - Divider line
  - Settings section: Project, Brands, Tracking, Account, Organization
- Bottom: User avatar + name + role, logout button

Sidebar background: `surface-soft` (#faf5e8). Active nav item: `surface-card` background with `ink` text and a 3px left border in `brand-teal`. Inactive: `body` text color.

**Topbar (top of content area, 64px):**
- Left: Breadcrumbs (e.g. "Dashboard" or "Settings > Brands")
- Right: Date range picker (pill tabs: 7d, 30d, 90d, custom), notification bell (future), user avatar small

**Content area:** Scrollable, max-width 1280px centered, padding `spacing.lg` (24px).

### 5. Dashboard Page (the main screen, most important)
This is what users see daily. It needs to communicate health at a glance.

**Top row: 4 MetricCards in a grid (2x2 on mobile, 4x1 on desktop)**
- **Visibility** (teal card `brand-teal`): "34.2%" large display number, "+5.2% vs last period" with a green up arrow, tiny sparkline
- **Avg Position** (lavender card `brand-lavender`): "2.8" large number, trend indicator
- **Sentiment** (peach card `brand-peach`): "72/100" large number, trend indicator
- **Share of Voice** (ochre card `brand-ochre`): "18.5%" large number, vs top competitor callout

Each MetricCard: colored background from the Clay palette, white text for dark cards (teal), dark text for light cards (lavender/peach/ochre), rounded-xl, padding-xl, the metric number in display-sm size, the label in caption-uppercase, trend in body-sm.

**Main chart area (full width card):**
Visibility over time line chart. X-axis: dates. Y-axis: visibility %. Multiple lines, one per platform, each in its platform color (pink=ChatGPT, teal=Perplexity, lavender=Gemini, ochre=AI Overviews, coral=Copilot). Legend below the chart. Recharts `AreaChart` with light gradient fills. Cream card background, rounded-lg.

**Below the chart, 2-column layout:**

Left column (60%): **Top Competitors** card. Table showing competitor brands ranked by visibility. Columns: Brand Name, Visibility %, Avg Position, Sentiment, 30d Trend (sparkline). Your brand highlighted with a subtle teal left border. Cream card, rounded-lg.

Right column (40%): **Top Cited Sources** card. Horizontal bar chart or ranked list of the top 10 domains AI models cite in your niche. Each entry: domain name, citation count, source type badge (e.g. "Reddit" in a pill badge, "Review Site" in another). Cream card, rounded-lg.

**Bottom row:** **Recent Activity** card. Last 5 scrape runs with status badges (green "Success", red "Failed", yellow "Running"). Shows prompt text truncated, platform badge, timestamp. "View all runs" link.

### 6. Prompts Page
**Top:** PageHeader with "Prompts" title, "Track the questions your customers ask AI" subtitle. "Add Prompt" primary button on the right.

**Filter bar:** Topic dropdown filter, tag multi-select filter, platform filter, status filter (Active/Paused/Archived). Search input to filter by prompt text.

**Main content:** Table view (default) with toggle to card view. Table columns: Prompt Text (truncated, clickable to expand), Topic (badge), Tags (pill badges), Status (colored badge), and then one mini-column per platform showing a visibility % or a dash if not tracked. Sortable by any column. Pagination at bottom.

**Click on a prompt row:** Expands inline or opens a slide-over panel showing:
- Full prompt text
- Per-platform latest results: visibility (yes/no mentioned), position, sentiment score, answer preview (first 200 chars)
- "View full answer" button that opens PromptResultModal showing the complete captured AI response with brand mentions highlighted in yellow, cited sources as clickable links, and sentiment reasoning

**Add/Edit Prompt form (modal):**
- Prompt text textarea
- Topic selector (dropdown, can create new inline)
- Tag multi-select (can create new inline)
- Platform selection (which platforms to track this prompt on)
- Country selection
- "Save" primary button, "Cancel" secondary

### 7. Sources Page
**Top:** PageHeader "Sources" with "See which websites AI trusts in your niche" subtitle.

**Filter bar:** Source type multi-select filter (Review Site, Reddit, Editorial, Corporate, UGC, Reference, Other), date range, platform filter.

**Top section:** Source Type Breakdown, a donut chart showing distribution of citations by source type. E.g. "Review Sites 42%, Reddit 22%, Editorial 18%, Corporate 12%, Other 6%." Each slice in a distinct color. Beside it: a summary callout card highlighting the #1 most cited domain.

**Main content:** Source Table. Columns: Domain, Citation Count (with bar indicator), Source Type (badge), Trend (sparkline over 30d), Platforms (which AI platforms cite this domain, shown as small colored dots). Sortable, paginated.

**Click on a domain row:** Expands to show all specific URLs from that domain that were cited, which prompts triggered citations to this domain, and whether you (the primary brand) are mentioned on this domain.

### 8. Competitors Page
**Top:** PageHeader "Competitors" with "See how you stack up in AI answers" subtitle.

**Main chart:** Share of Voice bar chart. Your brand vs all competitors, visibility % as horizontal bars, your brand in teal, competitors in muted gray. Or a donut showing share distribution.

**Comparison cards (horizontal scroll on mobile):** One card per brand (yours + competitors). Each card shows: brand name, visibility %, avg position, avg sentiment, trend sparkline. Your brand card has a teal left border or teal accent.

**Competitor Matrix:** Table where rows = prompts, columns = brands (you + competitors). Each cell shows: green check if mentioned, red X if not, or a position number. This is the "gap analysis" view: you can instantly see which prompts your competitors win and you don't.

**Gap Analysis callout:** A highlighted section that filters to only prompts where competitors appear but you don't. "You're missing from X prompts where [Competitor] appears." Actionable and attention-grabbing.

### 9. Project Settings Page
Standard settings form. Project name, website URL, edit and save. "Danger zone" at bottom with delete project (requires confirmation modal).

### 10. Brands Page (under Settings)
Card grid showing all brands in the project. Primary brand has a teal "Your Brand" badge. Competitors have a neutral "Competitor" badge. Each card: brand name, aliases listed, visibility % sparkline. "Add Competitor" button. Click to edit (name, aliases). Delete with confirmation.

### 11. Tracking Page (under Settings)
Shows all tracking configurations as a table: Prompt (truncated), Platform (colored badge), Country (flag emoji + code), Frequency (Daily/Weekly badge), Status (Active/Paused toggle). Bulk actions: select multiple and activate/pause. "Add Configuration" button opens a form to pick prompt(s) + platform(s) + country + frequency.

### 12. Run History Page
Table: Timestamp, Prompt (truncated), Platform (badge), Country, Status (colored badge: green Success, red Failed, yellow Running, gray Pending), Duration. Click a row to see the full raw captured answer, the parsed data (mentions found, sentiment scores, sources extracted), and optionally a screenshot if available.

### 13. Account Settings Page
User profile form: name, email (read-only or editable), change password section. Simple and clean.

### 14. Organization Settings Page (admin only)
Org name, member list table (name, email, role, joined date), invite member button, role change dropdown per member, remove member. Only visible to ADMIN and SUPER_ADMIN roles.

## Empty States
Every page needs an empty state for when there's no data yet:
- Dashboard with no metrics: illustration placeholder + "Set up tracking to see your AI visibility" + "Add Prompts" button
- Prompts page with no prompts: "Add your first prompt to start tracking" + "Add Prompt" button
- Sources with no data: "Sources will appear once your first tracking runs complete"
- Competitors with no competitors: "Add competitors to see how you compare" + "Add Competitor" button
- Run History with no runs: "No runs yet. Configure tracking to get started."

## Responsive Behavior
- **Desktop (1024px+):** Full sidebar (240px) + content area. Dashboard metrics 4-column grid. Tables show all columns.
- **Tablet (768-1024px):** Sidebar collapses to icons-only (64px) by default, expandable. Dashboard metrics 2x2 grid. Tables hide less-important columns.
- **Mobile (<768px):** Sidebar becomes a slide-out drawer triggered by hamburger menu. Dashboard metrics stack vertically. Tables become card-based lists. Charts are full-width with horizontal scroll if needed.

## Key Interactions
- **Project switching:** Dropdown in sidebar instantly switches all data. Use Zustand store + React Query invalidation.
- **Date range:** Global date range picker in topbar affects all charts and metrics on the current page.
- **Prompt result expansion:** Click a prompt row to see per-platform results inline, or open a full modal for the captured answer.
- **Real-time scrape status:** Run History page could poll for status updates on running scrapes (use TanStack Query's refetchInterval).
- **Toast notifications:** Success/error feedback on all CRUD operations.

## Platform Color Mapping (consistent everywhere)
- ChatGPT: brand-pink (#ff4d8b)
- Perplexity: brand-teal (#1a3a3a)
- Gemini: brand-lavender (#b8a4ed)
- Google AI Overviews: brand-ochre (#e8b94a)
- Copilot: brand-coral (#ff6b5a)

These colors are used for: chart lines/areas, platform badges, platform dots in tables, legend items. This mapping is a constant defined once in `config/platforms.js`.

## What to Build Per Milestone

**Milestone 1 frontend:** Auth pages (login, signup, verify, forgot/reset password). Onboarding wizard. AppShell layout (sidebar, topbar, content area). Project settings, brands, and prompts CRUD pages. Tracking configuration page. All wired to the FastAPI endpoints with TanStack Query. Empty states for dashboard, sources, competitors.

**Milestone 2-3 frontend:** Run History page with manual run button. Run detail view showing raw captured answers and parsed results.

**Milestone 6 frontend:** The full Dashboard page with all charts and metrics. Sources page with citation analytics. Competitors page with comparison matrix and gap analysis. This is where Recharts gets heavily used.

**Milestone 7 frontend:** Polish, loading skeletons, error boundaries, CSV export buttons, responsive refinements.

## API Integration Pattern

All API calls go through `config/api.js` which creates an Axios instance:
- Base URL from env var `VITE_API_URL`
- Request interceptor adds `Authorization: Bearer {token}` from Zustand auth store
- Response interceptor handles 401 (redirect to login, clear auth store)
- All endpoints scoped: `/api/projects/{project_id}/brands`, `/api/projects/{project_id}/prompts`, etc.

TanStack Query hooks in `/hooks/` wrap every API call with proper query keys, stale times, and cache invalidation on mutations.