# Cost Analysis Patterns

## Service Detection

### 1. Scan Configuration Files

```bash
# Find environment variables
grep -r "API_KEY\|SECRET\|TOKEN" .env* config/

# Find infrastructure definitions
find . -name "*.tf" -o -name "serverless.yml" -o -name "docker-compose.yml"
```

### 2. Scan Dependencies

```javascript
// package.json indicators
const COST_INDICATORS = {
  // Cloud providers
  'aws-sdk': 'AWS services',
  '@aws-sdk/*': 'AWS services',
  '@google-cloud/*': 'GCP services',
  '@azure/*': 'Azure services',
  
  // AI/ML
  'openai': 'OpenAI API',
  'anthropic': 'Anthropic API',
  'replicate': 'Replicate API',
  
  // Communications
  'twilio': 'Twilio SMS/Voice',
  '@sendgrid/mail': 'SendGrid Email',
  'postmark': 'Postmark Email',
  'nodemailer': 'Email (check provider)',
  
  // Payments
  'stripe': 'Stripe fees (2.9% + $0.30)',
  
  // Storage/Database
  '@prisma/client': 'Database (check provider)',
  'mongoose': 'MongoDB',
  '@supabase/supabase-js': 'Supabase',
  '@planetscale/*': 'PlanetScale',
  
  // Search
  'algoliasearch': 'Algolia',
  '@elastic/*': 'Elasticsearch',
  
  // Auth
  '@auth0/*': 'Auth0',
  'firebase-admin': 'Firebase',
  '@clerk/*': 'Clerk',
};
```

### 3. Scan Code for Usage

```typescript
// Find service instantiations
const SERVICE_PATTERNS = [
  /new S3Client/g,           // AWS S3
  /new OpenAI/g,             // OpenAI
  /Anthropic\(/g,            // Anthropic
  /twilio\.messages/g,       // Twilio SMS
  /sendgrid\.send/g,         // SendGrid
  /stripe\.(customers|subscriptions|charges)/g, // Stripe
];
```

## Common Service Pricing

### AI/ML Services

| Service | Cost | Unit |
|---------|------|------|
| OpenAI GPT-4 | $0.03 | per 1K input tokens |
| OpenAI GPT-4 | $0.06 | per 1K output tokens |
| OpenAI GPT-4o | $0.005 | per 1K input tokens |
| OpenAI GPT-4o | $0.015 | per 1K output tokens |
| OpenAI GPT-4o-mini | $0.00015 | per 1K input tokens |
| OpenAI Whisper | $0.006 | per minute audio |
| OpenAI DALL-E 3 | $0.04-0.12 | per image |
| Anthropic Claude Sonnet | $0.003 | per 1K input tokens |
| Anthropic Claude Sonnet | $0.015 | per 1K output tokens |
| Replicate (varies) | $0.0001-0.01 | per second GPU |

### Cloud Infrastructure

| Service | Cost | Unit |
|---------|------|------|
| AWS S3 Storage | $0.023 | per GB/month |
| AWS S3 Requests | $0.0004 | per 1K GET |
| AWS Lambda | $0.0000166 | per GB-second |
| AWS Lambda | $0.20 | per 1M requests |
| Vercel Pro | $20 | per month base |
| Vercel Functions | $0.40 | per 1M invocations |
| PlanetScale | $29 | per month (Scaler) |
| Supabase | $25 | per month (Pro) |

### Communications

| Service | Cost | Unit |
|---------|------|------|
| SendGrid | $0.00100 | per email (free tier: 100/day) |
| Twilio SMS | $0.0079 | per outbound SMS |
| Twilio Voice | $0.014 | per minute |
| Postmark | $0.00100 | per email |

### Auth Providers

| Service | Cost | Unit |
|---------|------|------|
| Auth0 | $0.00 | first 7,500 MAU free |
| Auth0 | $0.07 | per MAU (Essentials) |
| Clerk | $0.00 | first 10,000 MAU free |
| Clerk | $0.02 | per MAU beyond free |
| Firebase Auth | Free | unlimited |

### Payment Processing

| Service | Cost | Unit |
|---------|------|------|
| Stripe | 2.9% + $0.30 | per transaction |
| Stripe Billing | 0.5% | subscription revenue |
| PayPal | 2.99% + $0.49 | per transaction |

## Cost Calculation Patterns

### Per-User Cost Estimation

```typescript
interface CostBreakdown {
  fixed: {
    monthly: number;
    description: string;
  }[];
  perUser: {
    monthly: number;
    description: string;
  }[];
  perFeature: {
    feature: string;
    costPerUse: number;
    avgUsesPerUser: number;
  }[];
}

function calculateCostPerUser(costs: CostBreakdown, userCount: number): number {
  const totalFixed = costs.fixed.reduce((sum, c) => sum + c.monthly, 0);
  const fixedPerUser = totalFixed / userCount;
  
  const variablePerUser = costs.perUser.reduce((sum, c) => sum + c.monthly, 0);
  
  const featureCostPerUser = costs.perFeature.reduce(
    (sum, f) => sum + (f.costPerUse * f.avgUsesPerUser), 
    0
  );
  
  return fixedPerUser + variablePerUser + featureCostPerUser;
}
```

### Feature Cost Attribution

```typescript
// Map features to their cost drivers
const FEATURE_COSTS = {
  'ai_analysis': {
    services: ['openai'],
    estimatedCostPerUse: 0.03, // ~1K tokens in, 500 out
    category: 'high',
  },
  'pdf_export': {
    services: ['lambda', 'puppeteer'],
    estimatedCostPerUse: 0.01,
    category: 'medium',
  },
  'email_notification': {
    services: ['sendgrid'],
    estimatedCostPerUse: 0.001,
    category: 'low',
  },
  'file_upload': {
    services: ['s3'],
    estimatedCostPerUse: 0.001, // ~1MB avg
    category: 'low',
  },
  'sms_alert': {
    services: ['twilio'],
    estimatedCostPerUse: 0.008,
    category: 'medium',
  },
};
```

### Break-Even Analysis

```typescript
function calculateBreakEven(
  fixedCosts: number,      // Monthly fixed costs
  variableCostPerUser: number,
  pricePerUser: number
): number {
  // Break-even users = Fixed Costs / (Price - Variable Cost)
  const contribution = pricePerUser - variableCostPerUser;
  if (contribution <= 0) {
    throw new Error('Price must exceed variable cost per user');
  }
  return Math.ceil(fixedCosts / contribution);
}

// Example
const breakEvenUsers = calculateBreakEven(
  95,    // $95/month fixed
  0.50,  // $0.50/user variable
  9.00   // $9/user price
);
// Result: 12 users to break even
```

### Margin Calculation

```typescript
function calculateMargin(
  revenue: number,
  fixedCosts: number,
  variableCosts: number
): { grossMargin: number; netMargin: number } {
  const grossProfit = revenue - variableCosts;
  const netProfit = revenue - fixedCosts - variableCosts;
  
  return {
    grossMargin: (grossProfit / revenue) * 100,
    netMargin: (netProfit / revenue) * 100,
  };
}
```

## Cost Analysis Report Template

```markdown
# Cost Analysis Report

## Services Detected
| Service | Purpose | Pricing Model |
|---------|---------|---------------|
| [Service] | [Usage] | [$/unit] |

## Fixed Costs (Monthly)
| Item | Cost | Notes |
|------|------|-------|
| Hosting | $X | [Provider] |
| Database | $X | [Provider] |
| **Total** | **$X** | |

## Variable Costs (Per User/Month)
| Item | Cost | Calculation |
|------|------|-------------|
| Auth | $X | [MAU rate] |
| Storage | $X | [avg GB × rate] |
| **Total** | **$X/user** | |

## Feature Costs (Per Use)
| Feature | Cost | Avg Uses/User/Month |
|---------|------|---------------------|
| [Feature] | $X | X times |

## Pricing Recommendations
- **Minimum price** (break-even): $X/user
- **Recommended price** (60% margin): $X/user
- **Premium features**: Gate features costing >$X/use

## Tier Suggestions
| Tier | Features | Cost Basis | Suggested Price |
|------|----------|------------|-----------------|
| Free | [list] | <$0.50/user | $0 |
| Pro | [list] | ~$2/user | $9-15 |
| Enterprise | [list] | ~$10/user | $49+ |
```

## Automated Cost Scanning Script

```typescript
// Pseudocode for automated cost analysis
async function analyzeCosts(projectPath: string) {
  // 1. Detect services
  const packageJson = await readFile(`${projectPath}/package.json`);
  const envVars = await readFile(`${projectPath}/.env.example`);
  const services = detectServices(packageJson, envVars);
  
  // 2. Scan code for usage patterns
  const usagePatterns = await scanCodebase(projectPath, services);
  
  // 3. Estimate costs
  const costs = services.map(service => ({
    service,
    pricing: SERVICE_PRICING[service],
    estimatedUsage: usagePatterns[service],
    monthlyCost: calculateMonthlyCost(service, usagePatterns[service]),
  }));
  
  // 4. Generate report
  return generateCostReport(costs);
}
```
