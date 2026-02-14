# SPEC-1: Technical Architecture Deep Dive

## Overview

This document provides the technical implementation details for the AI App with Auto-Publish & Agent Marketing system described in SPEC-1.

---

## Technology Stack

### Frontend

**ChatGPT App:**
- OpenAI AI Studio / Apps SDK
- JSON-based action definitions
- OAuth 2.0 for user authentication
- Server-sent events for real-time updates

**Web Application:**
- Next.js 14+ (App Router)
- React 18+
- TypeScript
- Tailwind CSS
- shadcn/ui components
- React Query for data fetching

### Backend

**API Layer:**
- Next.js API routes (serverless)
- Alternative: Express.js / Fastify
- REST + GraphQL (optional)
- WebSockets for real-time features

**Core Services:**
- Node.js 20+ runtime
- TypeScript strict mode
- Zod for validation
- Prisma ORM (or Drizzle)

### Infrastructure

**Hosting:**
- Vercel (recommended for Next.js)
- Alternative: AWS Lambda + API Gateway
- Alternative: Railway / Render

**Database:**
- PostgreSQL 15+ (primary)
- Redis for caching & queues
- Alternative: PlanetScale MySQL

**Job Queue:**
- BullMQ (Redis-backed)
- Alternative: AWS SQS
- Alternative: Google Cloud Tasks

**Secrets Management:**
- AWS Secrets Manager (primary)
- Alternative: HashiCorp Vault
- Alternative: Azure Key Vault

### External Services

**AI & ML:**
- OpenAI API (GPT-4, DALL-E)
- Optional: Anthropic Claude
- Optional: Stability AI

**Payments:**
- Stripe (primary)
- Alternative: Paddle
- Alternative: LemonSqueezy

**Social Media:**
- Twitter API v2
- LinkedIn API
- Facebook Graph API (optional)
- Instagram Graph API (optional)

**Analytics:**
- PostHog (product analytics)
- Google Analytics 4
- Plausible (privacy-focused alternative)

**Monitoring:**
- Sentry (error tracking)
- Axiom / Better Stack (logging)
- Prometheus + Grafana (optional)

---

## System Architecture Details

### 1. ChatGPT App Integration

#### App Manifest Structure

```json
{
  "name": "Your App Name",
  "description": "Brief description for ChatGPT Apps directory",
  "version": "1.0.0",
  "api": {
    "type": "openapi",
    "url": "https://your-domain.com/openapi.json",
    "is_user_authenticated": true
  },
  "auth": {
    "type": "oauth",
    "client_url": "https://your-domain.com/api/auth/authorize",
    "authorization_url": "https://your-domain.com/api/auth/authorize",
    "authorization_content_type": "application/json",
    "verification_tokens": {
      "openai": "YOUR_VERIFICATION_TOKEN"
    }
  },
  "logo_url": "https://your-domain.com/logo.png",
  "contact_email": "support@your-domain.com",
  "legal_info_url": "https://your-domain.com/legal"
}
```

#### OpenAPI Specification

```yaml
openapi: 3.0.0
info:
  title: Your App API
  version: 1.0.0
  description: API for ChatGPT App integration

servers:
  - url: https://your-domain.com/api/v1

paths:
  /action/{actionName}:
    post:
      operationId: executeAction
      summary: Execute a specific action
      parameters:
        - name: actionName
          in: path
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Action executed successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  success:
                    type: boolean
                  data:
                    type: object
                  message:
                    type: string

components:
  securitySchemes:
    OAuth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://your-domain.com/api/auth/authorize
          tokenUrl: https://your-domain.com/api/auth/token
          scopes:
            read: Read access
            write: Write access

security:
  - OAuth2: [read, write]
```

#### Action Handlers

```typescript
// /api/v1/action/[actionName]/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { verifyOpenAIRequest } from '@/lib/auth';
import { executeAction } from '@/lib/actions';

export async function POST(
  req: NextRequest,
  { params }: { params: { actionName: string } }
) {
  try {
    // Verify request from OpenAI
    const user = await verifyOpenAIRequest(req);
    if (!user) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // Parse request body
    const body = await req.json();

    // Execute action
    const result = await executeAction(params.actionName, body, user);

    return NextResponse.json({
      success: true,
      data: result,
      message: 'Action completed successfully'
    });
  } catch (error) {
    console.error('Action execution error:', error);
    return NextResponse.json(
      { 
        success: false, 
        error: error.message 
      },
      { status: 500 }
    );
  }
}
```

---

### 2. Worker Automation System

#### Job Queue Architecture

```typescript
// lib/workers/queue.ts
import { Queue, Worker } from 'bullmq';
import Redis from 'ioredis';

const connection = new Redis(process.env.REDIS_URL!, {
  maxRetriesPerRequest: null,
  enableReadyCheck: false,
});

// Define job types
export enum JobType {
  GENERATE_CONTENT = 'generate-content',
  SCHEDULE_POST = 'schedule-post',
  MONITOR_ENGAGEMENT = 'monitor-engagement',
  TRACK_ANALYTICS = 'track-analytics',
}

// Content generation queue
export const contentQueue = new Queue('content', { connection });

// Scheduling queue
export const schedulingQueue = new Queue('scheduling', { connection });

// Engagement queue
export const engagementQueue = new Queue('engagement', { connection });

// Analytics queue
export const analyticsQueue = new Queue('analytics', { connection });

// Job data interfaces
export interface GenerateContentJob {
  userId: string;
  templateId: string;
  parameters: Record<string, any>;
  requiresApproval: boolean;
}

export interface SchedulePostJob {
  userId: string;
  contentId: string;
  platform: 'twitter' | 'linkedin' | 'facebook';
  scheduledTime: Date;
  content: {
    text: string;
    media?: string[];
  };
}

export interface MonitorEngagementJob {
  userId: string;
  platform: 'twitter' | 'linkedin';
  lastCheckTime: Date;
}

export interface TrackAnalyticsJob {
  userId: string;
  dateRange: { start: Date; end: Date };
  platforms: string[];
}
```

#### Worker Implementations

```typescript
// lib/workers/content-worker.ts
import { Worker, Job } from 'bullmq';
import { contentQueue, GenerateContentJob } from './queue';
import { generateContent } from '@/lib/ai/content-generator';
import { requiresHumanApproval } from '@/lib/compliance';
import { db } from '@/lib/db';

export const contentWorker = new Worker<GenerateContentJob>(
  'content',
  async (job: Job<GenerateContentJob>) => {
    const { userId, templateId, parameters, requiresApproval } = job.data;

    try {
      // Generate content using AI
      const content = await generateContent(templateId, parameters);

      // Check if approval needed
      const needsApproval = requiresApproval || 
                           await requiresHumanApproval(content, userId);

      if (needsApproval) {
        // Save to approval queue
        await db.contentApproval.create({
          data: {
            userId,
            content: content.text,
            media: content.media,
            status: 'pending',
            generatedAt: new Date(),
          },
        });

        return {
          status: 'pending_approval',
          contentId: content.id,
        };
      } else {
        // Auto-approve and schedule
        await db.content.create({
          data: {
            userId,
            ...content,
            status: 'approved',
          },
        });

        return {
          status: 'approved',
          contentId: content.id,
        };
      }
    } catch (error) {
      console.error('Content generation error:', error);
      throw error;
    }
  },
  { connection }
);

contentWorker.on('completed', (job) => {
  console.log(`Content job ${job.id} completed`);
});

contentWorker.on('failed', (job, err) => {
  console.error(`Content job ${job?.id} failed:`, err);
});
```

```typescript
// lib/workers/scheduling-worker.ts
import { Worker, Job } from 'bullmq';
import { schedulingQueue, SchedulePostJob } from './queue';
import { postToTwitter, postToLinkedIn } from '@/lib/social';
import { db } from '@/lib/db';

export const schedulingWorker = new Worker<SchedulePostJob>(
  'scheduling',
  async (job: Job<SchedulePostJob>) => {
    const { userId, contentId, platform, content } = job.data;

    try {
      let postId: string;

      // Post to platform
      switch (platform) {
        case 'twitter':
          postId = await postToTwitter(userId, content);
          break;
        case 'linkedin':
          postId = await postToLinkedIn(userId, content);
          break;
        default:
          throw new Error(`Unsupported platform: ${platform}`);
      }

      // Update content status
      await db.content.update({
        where: { id: contentId },
        data: {
          status: 'published',
          publishedAt: new Date(),
          platformPostId: postId,
          platform,
        },
      });

      return {
        status: 'published',
        postId,
      };
    } catch (error) {
      console.error('Scheduling error:', error);
      
      // Update content with error
      await db.content.update({
        where: { id: contentId },
        data: {
          status: 'failed',
          error: error.message,
        },
      });

      throw error;
    }
  },
  { connection }
);
```

#### Compliance & Rate Limiting

```typescript
// lib/compliance/rate-limiter.ts
import { Redis } from 'ioredis';

const redis = new Redis(process.env.REDIS_URL!);

interface RateLimit {
  platform: string;
  userId: string;
  maxRequests: number;
  windowSeconds: number;
}

export async function checkRateLimit(
  limit: RateLimit
): Promise<boolean> {
  const key = `ratelimit:${limit.platform}:${limit.userId}`;
  const current = await redis.incr(key);

  if (current === 1) {
    await redis.expire(key, limit.windowSeconds);
  }

  return current <= limit.maxRequests;
}

// Platform-specific limits (per their ToS)
export const PLATFORM_LIMITS = {
  twitter: {
    posts: { maxRequests: 50, windowSeconds: 86400 }, // 50/day
    replies: { maxRequests: 100, windowSeconds: 86400 },
    likes: { maxRequests: 1000, windowSeconds: 86400 },
  },
  linkedin: {
    posts: { maxRequests: 25, windowSeconds: 86400 }, // 25/day
    comments: { maxRequests: 50, windowSeconds: 86400 },
  },
};
```

---

### 3. Secrets Management

#### AWS Secrets Manager Integration

```typescript
// lib/secrets/aws-secrets.ts
import { 
  SecretsManagerClient, 
  GetSecretValueCommand 
} from '@aws-sdk/client-secrets-manager';

const client = new SecretsManagerClient({
  region: process.env.AWS_REGION || 'us-east-1',
});

interface SecretCache {
  value: string;
  expiresAt: number;
}

const cache = new Map<string, SecretCache>();
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

export async function getSecret(secretName: string): Promise<string> {
  // Check cache first
  const cached = cache.get(secretName);
  if (cached && cached.expiresAt > Date.now()) {
    return cached.value;
  }

  try {
    const command = new GetSecretValueCommand({
      SecretId: secretName,
    });

    const response = await client.send(command);
    const secret = response.SecretString!;

    // Cache the secret
    cache.set(secretName, {
      value: secret,
      expiresAt: Date.now() + CACHE_TTL_MS,
    });

    return secret;
  } catch (error) {
    console.error('Error fetching secret:', error);
    throw new Error(`Failed to fetch secret: ${secretName}`);
  }
}

// Typed secret getters
export async function getOpenAIKey(): Promise<string> {
  return getSecret('openai-api-key');
}

export async function getStripeKey(): Promise<string> {
  return getSecret('stripe-secret-key');
}

export async function getTwitterCredentials() {
  const secret = await getSecret('twitter-api-credentials');
  return JSON.parse(secret);
}
```

#### OIDC-based CI/CD

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

env:
  AWS_REGION: us-east-1

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole
          aws-region: ${{ env.AWS_REGION }}

      - name: Fetch secrets
        run: |
          aws secretsmanager get-secret-value \
            --secret-id openai-api-key \
            --query SecretString \
            --output text > .env.local

      - name: Deploy to Vercel
        env:
          VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
        run: |
          npx vercel --prod --token $VERCEL_TOKEN
```

---

### 4. Database Schema

```prisma
// prisma/schema.prisma
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

model User {
  id            String    @id @default(cuid())
  email         String    @unique
  name          String?
  createdAt     DateTime  @default(now())
  updatedAt     DateTime  @updatedAt
  
  // Subscription
  stripeCustomerId     String?
  stripeSubscriptionId String?
  subscriptionStatus   String?
  subscriptionTier     String   @default("free")
  
  // Usage tracking
  apiCallsUsed  Int      @default(0)
  apiCallsLimit Int      @default(100)
  
  // Relations
  content       Content[]
  approvals     ContentApproval[]
  analytics     Analytics[]
  socialAccounts SocialAccount[]
  
  @@index([email])
}

model SocialAccount {
  id           String   @id @default(cuid())
  userId       String
  platform     String   // 'twitter', 'linkedin', etc.
  accountId    String
  accountName  String
  accessToken  String   // Encrypted
  refreshToken String?  // Encrypted
  expiresAt    DateTime?
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt
  
  user         User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  @@unique([userId, platform, accountId])
  @@index([userId])
}

model Content {
  id              String   @id @default(cuid())
  userId          String
  text            String
  media           String[] // URLs to media
  platform        String
  status          String   // 'draft', 'pending', 'approved', 'published', 'failed'
  templateId      String?
  scheduledFor    DateTime?
  publishedAt     DateTime?
  platformPostId  String?
  error           String?
  metrics         Json?    // Engagement metrics
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt
  
  user            User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  @@index([userId, status])
  @@index([scheduledFor])
}

model ContentApproval {
  id          String   @id @default(cuid())
  userId      String
  content     String
  media       String[]
  status      String   @default("pending") // 'pending', 'approved', 'rejected'
  generatedAt DateTime
  reviewedAt  DateTime?
  reviewedBy  String?
  feedback    String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
  
  user        User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  @@index([userId, status])
}

model Analytics {
  id         String   @id @default(cuid())
  userId     String
  platform   String
  metric     String   // 'impressions', 'engagements', 'clicks', etc.
  value      Float
  date       DateTime
  metadata   Json?
  createdAt  DateTime @default(now())
  
  user       User     @relation(fields: [userId], references: [id], onDelete: Cascade)
  
  @@index([userId, platform, date])
}

model AuditLog {
  id        String   @id @default(cuid())
  userId    String?
  action    String
  resource  String
  details   Json?
  ipAddress String?
  userAgent String?
  createdAt DateTime @default(now())
  
  @@index([userId, createdAt])
  @@index([action, createdAt])
}
```

---

## Security Considerations

### Authentication & Authorization

1. **User Authentication:**
   - OAuth 2.0 for ChatGPT App
   - NextAuth.js for web app
   - JWT tokens with short expiry
   - Refresh token rotation

2. **API Security:**
   - Rate limiting per endpoint
   - Request signature verification
   - CORS configuration
   - Input validation (Zod)

3. **Secret Management:**
   - Never log secrets
   - Encrypt sensitive data at rest
   - Use environment variables
   - Rotate secrets regularly

### Data Protection

1. **Encryption:**
   - TLS 1.3 for all connections
   - Database encryption at rest
   - Encrypted backups
   - Field-level encryption for tokens

2. **Privacy:**
   - GDPR compliance
   - Data retention policies
   - User data export
   - Right to deletion

### Monitoring & Alerts

1. **Security Monitoring:**
   - Failed login attempts
   - Unusual API usage
   - Secret access patterns
   - Rate limit violations

2. **Incident Response:**
   - Automated alerts
   - Runbook documentation
   - Secret rotation procedures
   - Breach notification plan

---

## Deployment Architecture

### Production Setup

```
┌─────────────────────────────────────────┐
│           Cloudflare / CDN              │
│     (DDoS protection, caching)          │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│          Vercel Edge Network            │
│     (Next.js app, API routes)           │
└─────────────────┬───────────────────────┘
                  │
        ┌─────────┼─────────┐
        │         │         │
        ▼         ▼         ▼
┌───────────┐ ┌─────────┐ ┌──────────┐
│PostgreSQL │ │  Redis  │ │   AWS    │
│  (Neon)   │ │(Upstash)│ │ Secrets  │
└───────────┘ └─────────┘ └──────────┘
```

### Scaling Considerations

1. **Horizontal Scaling:**
   - Stateless API design
   - Multiple worker instances
   - Load balancing
   - Database read replicas

2. **Caching Strategy:**
   - Redis for session data
   - CDN for static assets
   - API response caching
   - Database query caching

3. **Performance Optimization:**
   - Database indexing
   - Query optimization
   - Image optimization
   - Code splitting

---

## Cost Estimates

### Monthly Infrastructure Costs (MVP)

| Service | Cost |
|---------|------|
| Vercel Pro | $20 |
| PostgreSQL (Neon) | $19 |
| Redis (Upstash) | $10 |
| AWS Secrets Manager | $1 |
| Sentry | $26 |
| **Total** | **~$76/month** |

### With 1,000 Active Users

| Service | Cost |
|---------|------|
| Vercel (bandwidth) | $50 |
| Database | $50 |
| Redis | $25 |
| OpenAI API | $100-500 |
| Monitoring | $50 |
| **Total** | **~$275-675/month** |

### Break-even Analysis

- At $9.99/month tier: Need 28 paying customers
- At 10% conversion: Need 280 active users
- Achievable in Month 2-3

---

## Testing Strategy

### Unit Tests
- Action handlers
- Worker functions
- Utility libraries
- 80%+ coverage goal

### Integration Tests
- API endpoint flows
- Database operations
- External API mocks
- Worker job processing

### E2E Tests
- ChatGPT app flows
- Web app user journeys
- Payment processing
- Critical paths only

### Manual Testing
- ChatGPT app in sandbox
- Social media posting (test accounts)
- Approval workflows
- Error scenarios

---

## Monitoring & Observability

### Key Metrics

**Application:**
- Request latency (p50, p95, p99)
- Error rate by endpoint
- API success rate
- Worker job completion time

**Business:**
- Daily active users
- Conversion rate
- Churn rate
- MRR growth

**Infrastructure:**
- Database connection pool
- Redis memory usage
- API rate limit utilization
- Secret fetch latency

### Dashboards

1. **Operations Dashboard:**
   - System health
   - Error rates
   - Performance metrics
   - Alert status

2. **Business Dashboard:**
   - User growth
   - Revenue metrics
   - Feature usage
   - Cohort analysis

3. **Security Dashboard:**
   - Failed auth attempts
   - Secret access logs
   - Rate limit hits
   - Anomaly detection

---

## Conclusion

This technical architecture provides a solid foundation for building a production-ready AI app with automated marketing capabilities. The design prioritizes:

✅ Security (secrets management, OIDC, encryption)  
✅ Scalability (horizontal scaling, caching, queues)  
✅ Compliance (rate limits, ToS checks, audit logs)  
✅ Reliability (error handling, retries, monitoring)  
✅ Maintainability (TypeScript, modular design, tests)

The stack is proven, the costs are manageable, and the architecture supports growth from MVP to scale.

---

*Document Version: 1.0*  
*Last Updated: 2025-11-02*  
*Next Review: After MVP launch*
