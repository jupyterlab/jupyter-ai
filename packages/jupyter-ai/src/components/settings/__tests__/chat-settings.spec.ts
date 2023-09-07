import { minifyPatchObject } from '../minify';

const COMPLEX_OBJECT = {
  primitive: 0,
  array: ['a'],
  object: { nested: { field: 0 } }
};

describe('minifyPatchObject', () => {
  test('returns empty object if patch is identical', () => {
    const obj = COMPLEX_OBJECT;
    const patch = JSON.parse(JSON.stringify(obj));

    expect(minifyPatchObject(obj, patch)).toEqual({});
  });

  test('returns empty object if patch is empty', () => {
    expect(minifyPatchObject(COMPLEX_OBJECT, {})).toEqual({});
  });

  test('returns patch if object is empty', () => {
    expect(minifyPatchObject({}, COMPLEX_OBJECT)).toEqual(COMPLEX_OBJECT);
  });

  test('should remove unchanged props from patch', () => {
    const obj = {
      unchanged: 'foo',
      changed: 'bar',
      nested: {
        unchanged: 'foo',
        changed: 'bar'
      }
    };
    const patch = {
      unchanged: 'foo',
      changed: 'baz',
      nested: {
        unchanged: 'foo',
        changed: 'baz'
      }
    };

    expect(minifyPatchObject(obj, patch)).toEqual({
      changed: 'baz',
      nested: {
        changed: 'baz'
      }
    });
  });

  test('defers to patch object when property types mismatch', () => {
    const obj = {
      api_keys: ['ANTHROPIC_API_KEY']
    };
    const patch = {
      api_keys: {
        OPENAI_API_KEY: 'foobar'
      }
    };

    expect(minifyPatchObject(obj, patch)).toEqual(patch);
  });
});
