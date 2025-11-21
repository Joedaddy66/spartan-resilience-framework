# SPEC-1: Quick Start Implementation Guide

## Welcome! Let's Get Building 🚀

This guide will take you from zero to a working MVP in the fastest, most pragmatic way possible. We're going to cut through the noise and focus on what actually matters for launch.

---

## Week 1: Foundation Setup

### Day 1: Environment & Tools

**1. Create GitHub Repository**
```bash
# Clone this repo and create feature branch
git checkout -b feature/chatgpt-app-mvp

# Set up directory structure
mkdir -p apps/chatgpt-app
mkdir -p apps/web-shell
mkdir -p apps/workers
mkdir -p packages/shared
```

**2. Initialize Next.js Web App**
```bash
cd apps/web-shell
npx create-next-app@latest . --typescript --tailwind --app --no-src-dir
npm install @stripe/stripe-js stripe
npm install next-auth
npm install prisma @prisma/client
npm install zod
npm install bullmq ioredis
```

**3. Set Up Secrets Management**

Create `.env.local` (never commit!):
```env
# Database
DATABASE_URL="postgresql://user:pass@localhost:5432/chatgpt_app"

# OpenAI
OPENAI_API_KEY="sk-..."

# Stripe
STRIPE_SECRET_KEY="sk_test_..."
STRIPE_PUBLISHABLE_KEY="pk_test_..."
STRIPE_WEBHOOK_SECRET="whsec_..."

# NextAuth
NEXTAUTH_SECRET="generate-with: openssl rand -base64 32"
NEXTAUTH_URL="http://localhost:3000"

# Redis
REDIS_URL="redis://localhost:6379"

# AWS (for secrets - optional for local dev)
AWS_REGION="us-east-1"
AWS_ACCESS_KEY_ID="..."
AWS_SECRET_ACCESS_KEY="..."
```

**4. Initialize Database**
```bash
# Create Prisma schema (see architecture doc)
npx prisma init
npx prisma db push
npx prisma generate
```

### Day 2-3: Core API Structure

**1. Create API Routes**

```typescript
// app/api/v1/action/[actionName]/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(
  req: NextRequest,
  { params }: { params: { actionName: string } }
) {
  try {
    const body = await req.json();
    
    // TODO: Add authentication
    // TODO: Add rate limiting
    // TODO: Implement action logic
    
    return NextResponse.json({
      success: true,
      message: `Action ${params.actionName} executed`
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    );
  }
}
```

**2. Set Up Authentication**

```typescript
// app/api/auth/[...nextauth]/route.ts
import NextAuth from 'next-auth';
import GoogleProvider from 'next-auth/providers/google';
import { PrismaAdapter } from '@auth/prisma-adapter';
import { prisma } from '@/lib/db';

export const authOptions = {
  adapter: PrismaAdapter(prisma),
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
  ],
  callbacks: {
    session: async ({ session, user }) => {
      session.user.id = user.id;
      return session;
    },
  },
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
```

**3. Create OpenAPI Spec**

```yaml
# public/openapi.json
openapi: 3.0.0
info:
  title: Your App API
  version: 1.0.0
paths:
  /api/v1/action/generate:
    post:
      operationId: generate
      summary: Generate content
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                prompt:
                  type: string
                  description: The generation prompt
                type:
                  type: string
                  enum: [text, image, code]
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
                properties:
                  result:
                    type: string
```

### Day 4-5: ChatGPT App Manifest

**1. Create App Manifest**

```json
// public/.well-known/ai-plugin.json
{
  "schema_version": "v1",
  "name_for_human": "Your App Name",
  "name_for_model": "your_app",
  "description_for_human": "Brief description for users",
  "description_for_model": "Detailed description for AI model",
  "auth": {
    "type": "oauth",
    "client_url": "https://your-domain.com/api/auth/authorize",
    "authorization_url": "https://your-domain.com/api/auth/authorize",
    "authorization_content_type": "application/json",
    "scope": "read write",
    "verification_tokens": {
      "openai": "your_verification_token_here"
    }
  },
  "api": {
    "type": "openapi",
    "url": "https://your-domain.com/openapi.json"
  },
  "logo_url": "https://your-domain.com/logo.png",
  "contact_email": "support@your-domain.com",
  "legal_info_url": "https://your-domain.com/terms"
}
```

**2. Test Locally**

```bash
# Start dev server
npm run dev

# Test OpenAPI endpoint
curl http://localhost:3000/openapi.json

# Test action endpoint
curl -X POST http://localhost:3000/api/v1/action/generate \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test", "type": "text"}'
```

---

## Week 2: Core Functionality

### Day 6-7: Implement Core AI Logic

**1. Create AI Service**

```typescript
// lib/ai/service.ts
import OpenAI from 'openai';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function generateContent(
  prompt: string,
  options: {
    type: 'text' | 'image' | 'code';
    maxTokens?: number;
  }
) {
  if (options.type === 'text' || options.type === 'code') {
    const completion = await openai.chat.completions.create({
      model: 'gpt-4',
      messages: [
        {
          role: 'system',
          content: 'You are a helpful assistant.'
        },
        {
          role: 'user',
          content: prompt
        }
      ],
      max_tokens: options.maxTokens || 500,
    });

    return completion.choices[0].message.content;
  } else if (options.type === 'image') {
    const image = await openai.images.generate({
      model: 'dall-e-3',
      prompt,
      n: 1,
      size: '1024x1024',
    });

    return image.data[0].url;
  }

  throw new Error(`Unsupported type: ${options.type}`);
}
```

**2. Implement Action Handlers**

```typescript
// lib/actions/handlers.ts
import { generateContent } from '@/lib/ai/service';
import { trackUsage } from '@/lib/analytics';

export async function handleGenerateAction(
  params: {
    prompt: string;
    type: 'text' | 'image' | 'code';
  },
  userId: string
) {
  // Check usage limits
  const usage = await checkUsageLimits(userId);
  if (usage.exceeded) {
    throw new Error('Usage limit exceeded. Please upgrade.');
  }

  // Generate content
  const result = await generateContent(params.prompt, {
    type: params.type,
  });

  // Track usage
  await trackUsage(userId, {
    action: 'generate',
    type: params.type,
    tokens: estimateTokens(params.prompt + result),
  });

  return {
    result,
    usage: {
      remaining: usage.remaining - 1,
      limit: usage.limit,
    },
  };
}

async function checkUsageLimits(userId: string) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { apiCallsUsed: true, apiCallsLimit: true },
  });

  return {
    exceeded: user.apiCallsUsed >= user.apiCallsLimit,
    remaining: user.apiCallsLimit - user.apiCallsUsed,
    limit: user.apiCallsLimit,
  };
}

function estimateTokens(text: string): number {
  // Rough estimate: ~4 characters per token
  return Math.ceil(text.length / 4);
}
```

### Day 8-9: Landing Page & Dashboard

**1. Landing Page**

```tsx
// app/page.tsx
import Link from 'next/link';
import { Button } from '@/components/ui/button';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <section className="container mx-auto px-4 py-20">
        <div className="text-center max-w-3xl mx-auto">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            Your AI Assistant, Everywhere
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Access powerful AI capabilities in ChatGPT and on the web.
            Generate content, automate tasks, and scale your creativity.
          </p>
          <div className="flex gap-4 justify-center">
            <Button size="lg" asChild>
              <Link href="/api/auth/signin">Get Started Free</Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link href="#features">Learn More</Link>
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="container mx-auto px-4 py-20">
        <h2 className="text-3xl font-bold text-center mb-12">
          Everything You Need
        </h2>
        <div className="grid md:grid-cols-3 gap-8">
          <FeatureCard
            title="Native ChatGPT App"
            description="Works seamlessly inside ChatGPT"
            icon="🤖"
          />
          <FeatureCard
            title="Web Dashboard"
            description="Full control from any browser"
            icon="🌐"
          />
          <FeatureCard
            title="Automated Marketing"
            description="AI workers promote your content"
            icon="📈"
          />
        </div>
      </section>

      {/* Pricing Section */}
      <section className="container mx-auto px-4 py-20">
        <h2 className="text-3xl font-bold text-center mb-12">
          Simple Pricing
        </h2>
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          <PricingCard
            tier="Free"
            price="$0"
            features={[
              '100 API calls/month',
              'Basic features',
              'Community support',
            ]}
          />
          <PricingCard
            tier="Pro"
            price="$9.99"
            features={[
              'Unlimited API calls',
              'All features',
              'Priority support',
              'Automation workers',
            ]}
            highlighted
          />
        </div>
      </section>
    </div>
  );
}

function FeatureCard({ title, description, icon }) {
  return (
    <div className="bg-white p-6 rounded-lg shadow-lg">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  );
}

function PricingCard({ tier, price, features, highlighted = false }) {
  return (
    <div className={`bg-white p-8 rounded-lg shadow-lg ${
      highlighted ? 'border-4 border-indigo-500' : ''
    }`}>
      <h3 className="text-2xl font-bold mb-2">{tier}</h3>
      <div className="text-4xl font-bold mb-6">
        {price}<span className="text-lg text-gray-600">/month</span>
      </div>
      <ul className="space-y-3 mb-8">
        {features.map((feature, i) => (
          <li key={i} className="flex items-center">
            <span className="mr-2">✓</span>
            {feature}
          </li>
        ))}
      </ul>
      <Button className="w-full" variant={highlighted ? 'default' : 'outline'}>
        Get Started
      </Button>
    </div>
  );
}
```

**2. User Dashboard**

```tsx
// app/dashboard/page.tsx
import { getServerSession } from 'next-auth';
import { redirect } from 'next/navigation';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import { UsageCard } from '@/components/dashboard/usage-card';
import { ContentList } from '@/components/dashboard/content-list';

export default async function Dashboard() {
  const session = await getServerSession(authOptions);
  
  if (!session) {
    redirect('/api/auth/signin');
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Dashboard</h1>
      
      <div className="grid md:grid-cols-2 gap-6 mb-8">
        <UsageCard userId={session.user.id} />
        <div className="bg-white p-6 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Quick Actions</h2>
          <div className="space-y-2">
            <Button className="w-full">Generate Content</Button>
            <Button className="w-full" variant="outline">
              Schedule Post
            </Button>
          </div>
        </div>
      </div>

      <ContentList userId={session.user.id} />
    </div>
  );
}
```

### Day 10: Stripe Integration

**1. Create Checkout Session**

```typescript
// app/api/checkout/route.ts
import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { getServerSession } from 'next-auth';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2023-10-16',
});

export async function POST(req: NextRequest) {
  const session = await getServerSession();
  
  if (!session?.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { priceId } = await req.json();

  const checkoutSession = await stripe.checkout.sessions.create({
    mode: 'subscription',
    payment_method_types: ['card'],
    line_items: [
      {
        price: priceId,
        quantity: 1,
      },
    ],
    success_url: `${process.env.NEXTAUTH_URL}/dashboard?success=true`,
    cancel_url: `${process.env.NEXTAUTH_URL}/dashboard?canceled=true`,
    customer_email: session.user.email,
    metadata: {
      userId: session.user.id,
    },
  });

  return NextResponse.json({ url: checkoutSession.url });
}
```

**2. Handle Webhooks**

```typescript
// app/api/webhooks/stripe/route.ts
import { NextRequest, NextResponse } from 'next/server';
import Stripe from 'stripe';
import { prisma } from '@/lib/db';

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!);

export async function POST(req: NextRequest) {
  const body = await req.text();
  const signature = req.headers.get('stripe-signature')!;

  let event: Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(
      body,
      signature,
      process.env.STRIPE_WEBHOOK_SECRET!
    );
  } catch (err) {
    return NextResponse.json(
      { error: 'Webhook signature verification failed' },
      { status: 400 }
    );
  }

  switch (event.type) {
    case 'checkout.session.completed':
      const session = event.data.object as Stripe.Checkout.Session;
      await handleCheckoutCompleted(session);
      break;
    case 'customer.subscription.updated':
      const subscription = event.data.object as Stripe.Subscription;
      await handleSubscriptionUpdated(subscription);
      break;
  }

  return NextResponse.json({ received: true });
}

async function handleCheckoutCompleted(session: Stripe.Checkout.Session) {
  const userId = session.metadata?.userId;
  
  if (!userId) return;

  await prisma.user.update({
    where: { id: userId },
    data: {
      stripeCustomerId: session.customer as string,
      stripeSubscriptionId: session.subscription as string,
      subscriptionStatus: 'active',
      subscriptionTier: 'pro',
      apiCallsLimit: 999999, // Unlimited for pro
    },
  });
}
```

---

## Week 3: Worker Automation

### Day 11-13: Job Queue Setup

**1. Initialize Redis & BullMQ**

```typescript
// lib/queue/connection.ts
import { Queue, Worker } from 'bullmq';
import Redis from 'ioredis';

export const connection = new Redis(process.env.REDIS_URL!, {
  maxRetriesPerRequest: null,
});

// Create queues
export const contentQueue = new Queue('content', { connection });
export const schedulingQueue = new Queue('scheduling', { connection });
export const analyticsQueue = new Queue('analytics', { connection });
```

**2. Content Generation Worker**

```typescript
// lib/workers/content-generator.ts
import { Worker } from 'bullmq';
import { connection, contentQueue } from '@/lib/queue/connection';
import { generateContent } from '@/lib/ai/service';
import { prisma } from '@/lib/db';

export const contentWorker = new Worker(
  'content',
  async (job) => {
    const { userId, templateId, parameters } = job.data;

    const content = await generateContent(parameters.prompt, {
      type: 'text',
    });

    // Save to approval queue
    await prisma.contentApproval.create({
      data: {
        userId,
        content,
        status: 'pending',
        generatedAt: new Date(),
      },
    });

    return { success: true, contentId: 'new-id' };
  },
  { connection }
);

// Start worker
contentWorker.on('completed', (job) => {
  console.log(`Job ${job.id} completed`);
});
```

**3. API Endpoint to Trigger Jobs**

```typescript
// app/api/workers/generate-content/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { contentQueue } from '@/lib/queue/connection';
import { getServerSession } from 'next-auth';

export async function POST(req: NextRequest) {
  const session = await getServerSession();
  
  if (!session?.user) {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
  }

  const { templateId, parameters } = await req.json();

  const job = await contentQueue.add('generate', {
    userId: session.user.id,
    templateId,
    parameters,
  });

  return NextResponse.json({
    success: true,
    jobId: job.id,
  });
}
```

### Day 14-15: Approval Workflow UI

**1. Approval Dashboard**

```tsx
// app/dashboard/approvals/page.tsx
import { getServerSession } from 'next-auth';
import { prisma } from '@/lib/db';
import { ApprovalCard } from '@/components/dashboard/approval-card';

export default async function ApprovalsPage() {
  const session = await getServerSession();
  
  const pendingApprovals = await prisma.contentApproval.findMany({
    where: {
      userId: session.user.id,
      status: 'pending',
    },
    orderBy: {
      generatedAt: 'desc',
    },
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">
        Pending Approvals ({pendingApprovals.length})
      </h1>
      
      {pendingApprovals.length === 0 ? (
        <p className="text-gray-600">No pending approvals</p>
      ) : (
        <div className="space-y-4">
          {pendingApprovals.map((approval) => (
            <ApprovalCard key={approval.id} approval={approval} />
          ))}
        </div>
      )}
    </div>
  );
}
```

**2. Approval Actions**

```typescript
// app/api/approvals/[id]/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { prisma } from '@/lib/db';
import { schedulingQueue } from '@/lib/queue/connection';

export async function PATCH(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const { action, scheduledTime, platform } = await req.json();

  const approval = await prisma.contentApproval.findUnique({
    where: { id: params.id },
  });

  if (!approval) {
    return NextResponse.json({ error: 'Not found' }, { status: 404 });
  }

  if (action === 'approve') {
    // Update approval
    await prisma.contentApproval.update({
      where: { id: params.id },
      data: {
        status: 'approved',
        reviewedAt: new Date(),
      },
    });

    // Schedule posting
    await schedulingQueue.add('post', {
      userId: approval.userId,
      content: approval.content,
      platform,
      scheduledTime: new Date(scheduledTime),
    });

    return NextResponse.json({ success: true });
  } else if (action === 'reject') {
    await prisma.contentApproval.update({
      where: { id: params.id },
      data: {
        status: 'rejected',
        reviewedAt: new Date(),
      },
    });

    return NextResponse.json({ success: true });
  }

  return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
}
```

---

## Week 4: Testing & Launch Prep

### Day 16-18: Testing

**1. Test ChatGPT App Locally**
```bash
# Use ngrok for testing
ngrok http 3000

# Update manifest with ngrok URL
# Test in ChatGPT plugin sandbox
```

**2. Test Payment Flow**
```bash
# Use Stripe test cards
# Card: 4242 4242 4242 4242
# Exp: Any future date
# CVC: Any 3 digits
```

**3. Test Worker Jobs**
```bash
# Trigger content generation
curl -X POST http://localhost:3000/api/workers/generate-content \
  -H "Content-Type: application/json" \
  -H "Cookie: your-session-cookie" \
  -d '{"templateId": "social-post", "parameters": {"prompt": "test"}}'

# Check job status in Redis
redis-cli
KEYS bull:content:*
```

### Day 19-20: Deploy & Submit

**1. Deploy to Production**
```bash
# Deploy to Vercel
vercel --prod

# Set environment variables
vercel env add OPENAI_API_KEY
vercel env add STRIPE_SECRET_KEY
# ... add all env vars
```

**2. Configure Domain**
```bash
# Add custom domain in Vercel
# Update DNS records
# Enable SSL
```

**3. Submit to ChatGPT Apps Directory**

- Go to OpenAI Platform
- Navigate to AI Studio
- Create new app
- Upload manifest
- Submit for review
- Wait 1-2 weeks for approval

**4. Launch Checklist**

- [ ] Production deployment live
- [ ] Database migrations run
- [ ] Stripe webhooks configured
- [ ] Domain SSL working
- [ ] ChatGPT app submitted
- [ ] Landing page live
- [ ] Analytics tracking enabled
- [ ] Error monitoring configured
- [ ] Social accounts created
- [ ] Beta users invited

---

## Post-Launch: First 30 Days

### Week 1 Post-Launch
- [ ] Monitor error rates
- [ ] Respond to user feedback
- [ ] Fix critical bugs
- [ ] Track sign-ups daily
- [ ] Engage on social media

### Week 2-3 Post-Launch
- [ ] Add requested features
- [ ] Optimize performance
- [ ] Improve onboarding
- [ ] Collect testimonials
- [ ] Plan content calendar

### Week 4 Post-Launch
- [ ] Analyze metrics
- [ ] Iterate on pricing
- [ ] Expand marketing
- [ ] Plan next features
- [ ] Prepare for scale

---

## Common Issues & Solutions

### Issue: OpenAI API Rate Limits
**Solution:** Implement exponential backoff, request queuing

### Issue: Stripe Webhook Failures
**Solution:** Add retry logic, monitor webhook dashboard

### Issue: Worker Job Failures
**Solution:** Dead letter queue, detailed error logging

### Issue: High Database Load
**Solution:** Add indexes, implement caching, use read replicas

### Issue: ChatGPT App Approval Delay
**Solution:** Start with web app, build audience while waiting

---

## Resources & Tools

### Development
- Next.js Docs: https://nextjs.org/docs
- OpenAI API: https://platform.openai.com/docs
- Stripe Docs: https://stripe.com/docs
- BullMQ Guide: https://docs.bullmq.io

### UI Components
- shadcn/ui: https://ui.shadcn.com
- Tailwind CSS: https://tailwindcss.com
- Radix UI: https://radix-ui.com

### Monitoring
- Sentry: https://sentry.io
- Vercel Analytics: https://vercel.com/analytics
- PostHog: https://posthog.com

### Community
- OpenAI Forum: https://community.openai.com
- Next.js Discord: https://nextjs.org/discord
- Indie Hackers: https://indiehackers.com

---

## Need Help?

**Common Questions:**

Q: How do I test the ChatGPT app locally?
A: Use ngrok to expose localhost, update manifest with ngrok URL

Q: How long does ChatGPT app approval take?
A: Typically 1-2 weeks, sometimes longer during high volume

Q: Can I launch without ChatGPT app approval?
A: Yes! Start with web app, submit app in parallel

Q: What if workers violate platform ToS?
A: Stay conservative with rate limits, require human approval

Q: How do I handle high traffic spikes?
A: Vercel auto-scales, add caching, optimize database queries

---

## You've Got This! 🎉

This guide gives you everything you need to go from zero to a working MVP. Remember:

✅ Start simple, iterate fast  
✅ Ship before it's perfect  
✅ Listen to users, adapt quickly  
✅ Focus on value, not features  
✅ Celebrate small wins  

Now stop reading and start building! The world needs what you're creating. 🚀

---

*Guide Version: 1.0*  
*Last Updated: 2025-11-02*  
*For: SPEC-1 Implementation*
