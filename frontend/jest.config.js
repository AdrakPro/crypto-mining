export default {
    testEnvironment: 'jsdom',
    roots: ['<rootDir>/src/', '<rootDir>/tests/'],
    testMatch: ['**/tests/**/*.js', '**/?(*.)+(spec|test).js'],
    collectCoverage: true,
    coverageDirectory: 'coverage',
    collectCoverageFrom: [
      'src/**/*.js',
      '!src/**/*.test.js',
    ],
  };