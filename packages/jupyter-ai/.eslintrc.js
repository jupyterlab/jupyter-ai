module.exports = {
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/eslint-recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:prettier/recommended'
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    tsconfigRootDir: __dirname,
    project: './tsconfig.json'
  },
  plugins: ['@stylistic', '@typescript-eslint'],
  rules: {
    '@typescript-eslint/naming-convention': [
      'error',
      {
        selector: 'interface',
        format: ['PascalCase'],
        custom: {
          regex: '^I[A-Z]',
          match: true
        }
      }
    ],
    '@typescript-eslint/no-unused-vars': ['warn', { args: 'none' }],
    '@typescript-eslint/no-explicit-any': 'off',
    '@typescript-eslint/no-namespace': 'off',
    '@typescript-eslint/no-use-before-define': 'off',
    '@stylistic/quotes': [
      'error',
      'single',
      { avoidEscape: true, allowTemplateLiterals: false }
    ],
    curly: ['error', 'all'],
    eqeqeq: 'error',
    'no-restricted-imports': [
      'error',
      {
        paths: [
          {
            name: '@mui/icons-material',

            message:
              "Please import icons using path imports, e.g. `import AddIcon from '@mui/icons-material/Add'`"
          }
        ],
        patterns: [
          {
            group: ['@mui/*/*/*'],
            message: '3rd level imports in mui are considered private'
          }
        ]
      }
    ],
    'prefer-arrow-callback': 'error'
  },
  overrides: [
    {
      files: ['src/**/*']
    }
  ]
};
