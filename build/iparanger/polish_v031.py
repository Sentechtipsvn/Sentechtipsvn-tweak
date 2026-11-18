#!/usr/bin/env python3
"""Polish v0.3.1 UI: symmetrical download accessory padding and optional iOS min metadata."""
from pathlib import Path
import sys

root=Path(sys.argv[1])
search=root/"Controllers/IPARSearchViewController.m"
s=search.read_text("utf-8")
a="button.frame = CGRectMake(0, 0, 48, 48);"
assert s.count(a)==1
s=s.replace(a,"button.frame = CGRectMake(0, 0, 48, 48);\n    UIView *accessoryContainer = [[UIView alloc] initWithFrame:CGRectMake(0, 0, 67, 48)];")
a="cell.accessoryView = button;"
assert s.count(a)==1
s=s.replace(a,"[accessoryContainer addSubview:button];\n    cell.accessoryView = accessoryContainer;")
search.write_text(s,"utf-8")

picker=root/"Controllers/IPARVersionPickerViewController.m"
s=picker.read_text("utf-8")
anchor='''    return [parts componentsJoinedByString:@"  ·  "];
}'''
assert s.count(anchor)==1
s=s.replace(anchor,r'''    // Version-history providers may expose minimum iOS under different keys.
    // Do NOT label older versions using the latest App Store minimumOSVersion.
    id requirement = nil;
    for (NSString *key in @[@"minimumOSVersion", @"minimum_os_version",
                             @"minimumOsVersion", @"minimumSystemVersion",
                             @"minimum_ios_version", @"min_os_version"]) {
        id candidate = version[key];
        if ([candidate isKindOfClass:[NSString class]] && [candidate length] > 0) {
            requirement = candidate;
            break;
        }
    }
    if (requirement && [requirement isKindOfClass:[NSString class]]) {
        NSString *min = [requirement stringByTrimmingCharactersInSet:
                        NSCharacterSet.whitespaceAndNewlineCharacterSet];
        NSCharacterSet *valid = [NSCharacterSet characterSetWithCharactersInString:@"0123456789."];
        if (min.length > 0 && [min rangeOfCharacterFromSet:valid.invertedSet].location == NSNotFound) {
            [parts addObject:[NSString stringWithFormat:IPARL(@"iOS %@+"), min]];
        }
    }
    return [parts componentsJoinedByString:@"  ·  "];
}''')
if '#import "../Utils/IPARLanguageManager.h"' not in s:
    s='#import "../Utils/IPARLanguageManager.h"\n'+s
picker.write_text(s,"utf-8")
print("Aligned download accessory, added only source-grounded per-version iOS requirements")
