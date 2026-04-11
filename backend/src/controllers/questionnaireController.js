const UserProfile = require('../models/UserProfile');

const submitQuestionnaire = async (req, res) => {
  try {
    const { responses, user_id, datasetRef } = req.body;

    // Resolve persona from questionnaire answers
    const audience = responses.find(r => r.id === 'audience')?.value;
    const trust = responses.find(r => r.id === 'trust')?.value;
    const instinct = responses.find(r => r.id === 'instinct')?.value;
    const visual = responses.find(r => r.id === 'visual')?.value;

    let user_type = 'Beginner';
    if (audience === 'regulators') user_type = 'Compliance';
    else if (audience === 'board') user_type = 'Executive';
    else if (audience === 'me' && (trust === 'raw_math' || instinct === 'verify')) user_type = 'Analyst';
    else if (audience === 'team' && (instinct === 'fix' || instinct === 'explain')) user_type = 'SME';
    else if (audience === 'me' && (trust === 'actionable' || trust === 'trend')) user_type = 'Everyday';
    else if (audience === 'team') user_type = 'Everyday';

    // Persist user profile with questionnaire answers to MongoDB
    if (user_id) {
      await UserProfile.findOneAndUpdate(
        { username: user_id },
        {
          $set: {
            personaTier: user_type,
            hasCompletedOnboarding: true,
            datasetRef: datasetRef || null,
            questionnaireAnswers: { audience, trust, instinct, visual }
          }
        },
        { upsert: true, returnDocument: 'after' }
      );
    }

    res.status(200).json({
      user_type,
      complexity_level: 3
    });
  } catch (error) {
    console.error('[questionnaireController] Error:', error.message);
    res.status(500).json({ error: error.message });
  }
};

module.exports = { submitQuestionnaire };
