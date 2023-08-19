import { AiService } from '../../handler';

/**
 * Function that minimizes the `UpdateConfigRequest` object prior to submission.
 * Removes properties with values identical to those specified in the server
 * configuration.
 */
export function minifyUpdate(
  config: AiService.DescribeConfigResponse,
  update: AiService.UpdateConfigRequest
): AiService.UpdateConfigRequest {
  return minifyPatchObject(config, update) as AiService.UpdateConfigRequest;
}

/**
 * Function that removes all properties from `patch` that have identical values
 * to `obj` recursively.
 */
export function minifyPatchObject(
  obj: Record<string, any>,
  patch: Record<string, any>
): Record<string, any> {
  const diffObj: Record<string, any> = {};
  for (const key in patch) {
    if (!(key in obj) || typeof obj[key] !== typeof patch[key]) {
      // if key is not present in oldObj, or if the value types do not match,
      // use the value of `patch`.
      diffObj[key] = patch[key];
      continue;
    }

    const objVal = obj[key];
    const patchVal = patch[key];
    if (Array.isArray(objVal) && Array.isArray(patchVal)) {
      // if objects are both arrays but are not equal, then use the value
      const areNotEqual =
        objVal.length !== patchVal.length ||
        !objVal.every((objVal_i, i) => objVal_i === patchVal[i]);
      if (areNotEqual) {
        diffObj[key] = patchVal;
      }
    } else if (typeof patchVal === 'object') {
      // if the value is an object, run `diffObjects` recursively.
      const childPatch = minifyPatchObject(objVal, patchVal);
      const isNonEmpty = !!Object.keys(childPatch)?.length;
      if (isNonEmpty) {
        diffObj[key] = childPatch;
      }
    } else if (objVal !== patchVal) {
      // otherwise, use the value of `patch` only if it differs.
      diffObj[key] = patchVal;
    }
  }

  return diffObj;
}
