const mongoose = require('mongoose');

const userProfileSchema = new mongoose.Schema({
    username: {
        type: String,
        required: true,
        unique: true
    },
    personaTier: {
        type: String,
        enum: ['Beginner', 'Everyday', 'SME', 'Executive', 'Analyst', 'Compliance'],
        default: 'Beginner'
    },
    hasCompletedOnboarding: {
        type: Boolean,
        default: false
    },
    datasetRef: {
        type: String,
        default: null
    },
    complexityScore: {
        type: Number,
        min: 1,
        max: 5,
        default: 2
    },
    questionnaireAnswers: {
        audience: String,
        trust: String,
        instinct: String,
        visual: String
    }
}, { timestamps: true });

module.exports = mongoose.model('UserProfile', userProfileSchema);