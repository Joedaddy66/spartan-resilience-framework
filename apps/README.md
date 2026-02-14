# Apps Directory

This directory contains the application components for the Spartan Resilience Framework AI App implementation (SPEC-1).

## Structure

```
apps/
├── chatgpt-app/       # ChatGPT-native app configuration and assets
├── web-shell/         # Next.js web application
├── workers/           # Background automation workers
└── README.md          # This file
```

## Applications

### ChatGPT App (`chatgpt-app/`)

**Purpose:** Native ChatGPT application for seamless AI interaction

**Key Files:**
- `ai-plugin.json` - App manifest for ChatGPT Apps directory
- `openapi.json` - API specification for ChatGPT integration
- `logo.png` - App logo (512x512px)
- `README.md` - Setup and submission guide

**Status:** 🔄 To be implemented (see SPEC-1-QUICK-START.md)

### Web Shell (`web-shell/`)

**Purpose:** Web-based dashboard and landing page for users outside ChatGPT

**Tech Stack:**
- Next.js 14+ with App Router
- TypeScript
- Tailwind CSS
- Prisma ORM
- NextAuth.js for authentication
- Stripe for payments

**Key Features:**
- Landing page with pricing
- User dashboard
- Usage tracking
- Payment integration
- Content approval workflow

**Status:** 🔄 To be implemented (see SPEC-1-QUICK-START.md)

### Workers (`workers/`)

**Purpose:** Background automation agents for marketing and analytics

**Tech Stack:**
- BullMQ for job queues
- Redis for state management
- OpenAI API for content generation
- Social media platform APIs

**Worker Types:**
1. **Content Generator** - Creates promotional content with AI
2. **Scheduler** - Manages posting calendar and execution
3. **Engagement Monitor** - Tracks and suggests responses
4. **Analytics Tracker** - Collects and reports metrics

**Status:** 🔄 To be implemented (see SPEC-1-QUICK-START.md)

## Getting Started

### Prerequisites

- Node.js 20+
- PostgreSQL 15+
- Redis 7+
- OpenAI API key
- Stripe account (for payments)
- AWS account (for secrets management)

### Quick Setup

1. **Clone and navigate:**
   ```bash
   cd apps/web-shell
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Set up environment:**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your secrets
   ```

4. **Initialize database:**
   ```bash
   npx prisma db push
   npx prisma generate
   ```

5. **Start development server:**
   ```bash
   npm run dev
   ```

6. **Start workers (separate terminal):**
   ```bash
   npm run workers
   ```

## Documentation

Comprehensive documentation for SPEC-1 implementation:

- **[SPEC-1: Main Specification](../docs/SPEC-1-AI-APP-AUTO-PUBLISH.md)**  
  Complete project specification with market evaluation, requirements, and strategy

- **[SPEC-1: Technical Architecture](../docs/SPEC-1-TECHNICAL-ARCHITECTURE.md)**  
  Detailed technical design, stack choices, and implementation patterns

- **[SPEC-1: Quick Start Guide](../docs/SPEC-1-QUICK-START.md)**  
  Week-by-week implementation guide from zero to MVP

## Development Workflow

### Local Development

1. **Start infrastructure:**
   ```bash
   # Terminal 1: PostgreSQL + Redis (via Docker)
   docker-compose up postgres redis

   # Terminal 2: Web app
   cd apps/web-shell
   npm run dev

   # Terminal 3: Workers
   cd apps/workers
   npm run dev
   ```

2. **Test ChatGPT integration:**
   ```bash
   # Use ngrok for local testing
   ngrok http 3000
   # Update manifest with ngrok URL
   ```

### Testing

```bash
# Run unit tests
npm test

# Run integration tests
npm run test:integration

# Run E2E tests
npm run test:e2e
```

### Deployment

```bash
# Deploy web app to Vercel
vercel --prod

# Deploy workers to AWS Lambda (or Railway)
npm run deploy:workers
```

## Security

### Secrets Management

- **Never commit secrets** to version control
- Use AWS Secrets Manager for production
- Use `.env.local` for local development (gitignored)
- Rotate secrets regularly
- Use OIDC for CI/CD authentication

### Compliance

- Rate limiting on all external APIs
- Human-in-the-loop approval for sensitive actions
- Audit logging for all automated actions
- Platform ToS compliance checks
- GDPR-compliant data handling

## Monitoring

### Key Metrics

**Application:**
- API request latency
- Error rates by endpoint
- Worker job completion times
- Database query performance

**Business:**
- Daily active users
- Conversion rate (free to paid)
- Monthly recurring revenue
- Feature usage statistics

**Infrastructure:**
- Database connection pool utilization
- Redis memory usage
- API rate limit consumption
- Secret fetch latency

### Dashboards

1. **Vercel Dashboard** - Deployment and performance
2. **Sentry** - Error tracking and alerts
3. **PostHog** - Product analytics
4. **Stripe Dashboard** - Payment and subscription metrics

## Architecture Decisions

### Why Next.js?

- Server-side rendering for SEO
- API routes for backend logic
- Serverless deployment on Vercel
- Excellent developer experience
- Large ecosystem and community

### Why BullMQ?

- Reliable Redis-backed queues
- Built-in retry mechanisms
- Job prioritization
- Rate limiting support
- Active development and support

### Why Prisma?

- Type-safe database access
- Auto-generated types
- Migration management
- Excellent DX with VS Code
- Multi-database support

## Roadmap

### Phase 1: MVP (Weeks 1-4)
- [ ] Core ChatGPT app functionality
- [ ] Basic web dashboard
- [ ] Content generation worker
- [ ] Stripe payment integration
- [ ] Submit to ChatGPT Apps directory

### Phase 2: Growth (Months 2-3)
- [ ] Full worker automation suite
- [ ] Advanced analytics dashboard
- [ ] Multi-platform social integration
- [ ] Referral program
- [ ] Mobile-responsive improvements

### Phase 3: Scale (Months 4-6)
- [ ] Usage-based pricing tiers
- [ ] Team collaboration features
- [ ] API for third-party developers
- [ ] White-label options
- [ ] Enterprise features

## Contributing

### Code Style

- TypeScript strict mode
- ESLint + Prettier for formatting
- Conventional commits for git messages
- Comprehensive JSDoc comments

### Pull Request Process

1. Create feature branch from `main`
2. Implement changes with tests
3. Run linting and tests locally
4. Submit PR with clear description
5. Address review feedback
6. Merge after approval

## Support

### Need Help?

- 📖 [Read the documentation](../docs/)
- 💬 [Join discussions](https://github.com/Joedaddy66/spartan-resilience-framework/discussions)
- 🐛 [Report issues](https://github.com/Joedaddy66/spartan-resilience-framework/issues)
- 📧 [Email support](mailto:support@example.com)

### Common Issues

**Q: Database connection errors**  
A: Check PostgreSQL is running and DATABASE_URL is correct

**Q: Worker jobs not processing**  
A: Verify Redis is running and workers are started

**Q: ChatGPT app not loading**  
A: Check OpenAPI spec is valid and accessible

**Q: Payment webhook failures**  
A: Verify Stripe webhook secret is configured correctly

## License

See [LICENSE](../LICENSE) file in repository root.

---

**Status:** 🏗️ Under active development  
**Version:** 1.0.0-alpha  
**Last Updated:** 2025-11-02
