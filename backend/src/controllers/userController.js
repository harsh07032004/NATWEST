const UserProfile = require('../models/UserProfile');

// @desc    Get or create user profile. Returns isNewUser flag so frontend knows
//          whether to show onboarding or restore the returning user's persona.
// @route   POST /api/users
const getUserProfile = async (req, res) => {
    try {
        const { username } = req.body;

        if (!username) {
            return res.status(400).json({ message: 'Username is required' });
        }

        // Try to find the user
        let user = await UserProfile.findOne({ username });
        let isNewUser = false;

        // If user doesn't exist, create a new profile
        if (!user) {
            isNewUser = true;
            user = await UserProfile.create({
                username,
                personaTier: 'Beginner',
                complexityScore: 2
            });
        }

        res.status(200).json({ ...user.toObject(), isNewUser });
    } catch (error) {
        console.error(error);
        res.status(500).json({ message: 'Server Error' });
    }
};

module.exports = { getUserProfile };