const { generateExecutionPlan } = require('./backend/src/services/orchestratorService');
require('dotenv').config({ path: './backend/.env' });

async function test() {
    const plan = await generateExecutionPlan("show sales and why did they drop", "data/Superstore.csv");
    console.log(JSON.stringify(plan, null, 2));
}

test().catch(console.error);
