#!/usr/bin/env python3
"""Add on-device IPA audit: streamed SHA-256; ZIP integrity; CFBundle metadata;
Mach-O LC_ENCRYPTION_INFO(_64) across main app, PlugIns and frameworks.
No DRM removal, extracted binaries are removed immediately. Do not load entire IPA.
"""
from pathlib import Path
import json,sys
root=Path(sys.argv[1])
(root/"Utils/IPARIPAAudit.h").write_text(r'''#import <Foundation/Foundation.h>
@interface IPARIPAAudit : NSObject
+ (NSDictionary<NSString *, id> *)inspectFileAtPath:(NSString *)path;
@end
''',"utf-8")
(root/"Utils/IPARIPAAudit.m").write_text(r'''#import "IPARIPAAudit.h"
#import "../Extensions/IPARConstants.h"
#import <CommonCrypto/CommonDigest.h>
#import <mach-o/loader.h>
#import <mach-o/fat.h>
#import <libkern/OSByteOrder.h>

static BOOL IPARRunUnzip(NSArray<NSString *> *args, NSString *output) {
    NSString *path=kLaunchPathUnzip;
    if (![[NSFileManager defaultManager] isExecutableFileAtPath:path]) return NO;
    NSTask *task=[[NSTask alloc] init];
    task.launchPath=path;
    task.arguments=args;
    NSFileManager *fm=[NSFileManager defaultManager];
    [fm createFileAtPath:output contents:nil attributes:nil];
    NSFileHandle *file=[NSFileHandle fileHandleForWritingAtPath:output];
    if (!file) return NO;
    task.standardOutput=file;
    task.standardError=[NSFileHandle fileHandleWithNullDevice];
    BOOL good=NO;
    @try {
        [task launch];
        [task waitUntilExit];
        good=task.terminationStatus==0;
    } @catch (NSException *exception) {
        good=NO;
    }
    [file closeFile];
    return good;
}
static NSString *IPARSHA256File(NSString *path) {
    NSInputStream *stream=[NSInputStream inputStreamWithFileAtPath:path];
    if (!stream) return nil;
    [stream open];
    if (stream.streamStatus==NSStreamStatusError) return nil;
    CC_SHA256_CTX hash; CC_SHA256_Init(&hash);
    uint8_t buf[65536]; NSInteger count=0;
    while ((count=[stream read:buf maxLength:sizeof(buf)])>0) {
        CC_SHA256_Update(&hash,buf,(CC_LONG)count);
    }
    [stream close];
    if (count<0) return nil;
    unsigned char digest[CC_SHA256_DIGEST_LENGTH];
    CC_SHA256_Final(digest,&hash);
    NSMutableString *out=[NSMutableString stringWithCapacity:CC_SHA256_DIGEST_LENGTH*2];
    for (NSUInteger i=0;i<CC_SHA256_DIGEST_LENGTH;i++) [out appendFormat:@"%02x",digest[i]];
    return out;
}
static BOOL IPARScanThinMachO(const uint8_t *buf, size_t length, size_t start,
                             BOOL *encrypted, BOOL *recognized) {
    if (start+sizeof(uint32_t)>length) return NO;
    uint32_t magic;memcpy(&magic,buf+start,4);
    BOOL is64=(magic==MH_MAGIC_64);
    BOOL is32=(magic==MH_MAGIC);
    if (!is64 && !is32) return NO;
    size_t header=is64?sizeof(struct mach_header_64):sizeof(struct mach_header);
    if (header>length-start) return NO;
    uint32_t ncmds=0,cmdbytes=0;
    memcpy(&ncmds,buf+start+16,4);
    memcpy(&cmdbytes,buf+start+20,4);
    if (ncmds>4096 || cmdbytes>4*1024*1024 || header+cmdbytes>length-start) return NO;
    *recognized=YES;
    size_t offset=start+header;
    for (uint32_t i=0;i<ncmds;++i) {
        if (offset+sizeof(struct load_command)>length) return NO;
        struct load_command cmd;memcpy(&cmd,buf+offset,sizeof(cmd));
        if (cmd.cmdsize<sizeof(cmd) || cmd.cmdsize>length-offset) return NO;
        if (cmd.cmd==LC_ENCRYPTION_INFO_64 && cmd.cmdsize>=sizeof(struct encryption_info_command_64)) {
            struct encryption_info_command_64 enc;memcpy(&enc,buf+offset,sizeof(enc));
            if (enc.cryptid!=0) *encrypted=YES;
        }
        if (cmd.cmd==LC_ENCRYPTION_INFO && cmd.cmdsize>=sizeof(struct encryption_info_command)) {
            struct encryption_info_command enc;memcpy(&enc,buf+offset,sizeof(enc));
            if (enc.cryptid!=0) *encrypted=YES;
        }
        offset+=cmd.cmdsize;
    }
    return YES;
}
static BOOL IPARScanMachO(NSString *path, BOOL *encrypted, BOOL *recognized) {
    NSError *e=nil;
    NSData *data=[NSData dataWithContentsOfFile:path options:NSDataReadingMappedIfSafe error:&e];
    if (!data || data.length<32) return NO;
    const uint8_t *buf=data.bytes;size_t len=data.length;
    uint32_t magic;memcpy(&magic,buf,4);
    if (magic==MH_MAGIC_64 || magic==MH_MAGIC)
        return IPARScanThinMachO(buf,len,0,encrypted,recognized);
    if (magic==FAT_MAGIC || magic==FAT_CIGAM) {
        // Universal binary: all architecture slices must have readable load commands.
        if (len<sizeof(struct fat_header)) return NO;
        struct fat_header fh;memcpy(&fh,buf,sizeof(fh));
        uint32_t count=OSSwapBigToHostInt32(fh.nfat_arch);
        if (count==0 || count>24 || sizeof(fh)+count*sizeof(struct fat_arch)>len) return NO;
        BOOL any=NO;
        for (uint32_t i=0;i<count;i++) {
            struct fat_arch arch;
            memcpy(&arch,buf+sizeof(fh)+i*sizeof(arch),sizeof(arch));
            uint32_t offset=OSSwapBigToHostInt32(arch.offset);
            uint32_t size=OSSwapBigToHostInt32(arch.size);
            if (offset>len || size>len-offset) return NO;
            BOOL found=NO;
            if (!IPARScanThinMachO(buf,len,offset,encrypted,&found)) return NO;
            any|=found;
        }
        *recognized=any;
        return any;
    }
    return NO;
}
static NSString *IPARFindTempPath(void) {
    return [NSTemporaryDirectory() stringByAppendingPathComponent:
       [NSString stringWithFormat:@"ipar-audit-%@",NSUUID.UUID.UUIDString]];
}
static BOOL IPARIsSafeZipName(NSString *name) {
    if (![name isKindOfClass:[NSString class]] || name.length==0) return NO;
    if ([name hasPrefix:@"/"] || [name containsString:@"\\"]) return NO;
    for (NSString *component in [name componentsSeparatedByString:@"/"])
        if ([component isEqualToString:@".."]) return NO;
    return YES;
}
static NSString *IPARFindFileInZip(NSArray<NSString *> *names,NSString *name) {
    for (NSString *item in names) if ([item isEqualToString:name]) return item;
    return nil;
}
static BOOL IPARUnzipEntry(NSString *archive,NSString *entry,NSString *destination) {
    return IPARRunUnzip(@[@"-p",archive,entry],destination);
}
static NSDictionary *IPARPlistForEntry(NSString *archive,NSString *entry) {
    NSString *temp=IPARFindTempPath();
    BOOL success=IPARUnzipEntry(archive,entry,temp);
    NSData *data=success?[NSData dataWithContentsOfFile:temp options:0 error:nil]:nil;
    [[NSFileManager defaultManager] removeItemAtPath:temp error:nil];
    if (!data || data.length>2*1024*1024) return nil;
    id property=[NSPropertyListSerialization propertyListWithData:data options:NSPropertyListImmutable format:NULL error:nil];
    return [property isKindOfClass:[NSDictionary class]]?property:nil;
}
@implementation IPARIPAAudit
+ (NSDictionary<NSString *, id> *)inspectFileAtPath:(NSString *)path {
    NSString *sha=IPARSHA256File(path);
    NSMutableDictionary *out=[@{@"sha":sha ?: @"—",
                                @"zip":@"unknown",
                                @"drm":@"unknown",
                                @"troll":@"unknown",
                                @"minIOS":@"—",
                                @"bundle":@"",
                                @"version":@"",
                                @"executables":@0,
                                @"plugins":@0,
                                @"frameworks":@0} mutableCopy];
    // Use the same unzip executable that the original IPARanger already uses.
    NSString *listing=IPARFindTempPath();
    BOOL hasList=IPARRunUnzip(@[@"-Z",@"-1",path],listing);
    NSData *namesData=hasList?[NSData dataWithContentsOfFile:listing]:nil;
    [[NSFileManager defaultManager] removeItemAtPath:listing error:nil];
    if (!namesData || namesData.length>8*1024*1024) return out;
    NSString *text=[[NSString alloc] initWithData:namesData encoding:NSUTF8StringEncoding];
    if (!text) return out;
    NSMutableArray *names=[NSMutableArray array];
    for (NSString *name in [text componentsSeparatedByCharactersInSet:NSCharacterSet.newlineCharacterSet]) {
        if (!name.length) continue;
        if (!IPARIsSafeZipName(name)) return out;
        [names addObject:name];
        if (names.count>50000) return out;
    }
    NSString *mainPlist=nil;
    for (NSString *name in names) {
        if ([name hasPrefix:@"Payload/"] && [name hasSuffix:@".app/Info.plist"]
            && [[name componentsSeparatedByString:@"/"] count]==3) {mainPlist=name;break;}
    }
    if (!mainPlist) {
        out[@"zip"]=@"invalid";return out;
    }
    // Verify all ZIP entries' CRC; on large archives this can be expensive, so
    // always run from a background queue (caller responsibility).
    NSString *test=IPARFindTempPath();
    BOOL zipValid=IPARRunUnzip(@[@"-tqq",path],test);
    [[NSFileManager defaultManager] removeItemAtPath:test error:nil];
    out[@"zip"]=zipValid?@"valid":@"invalid";
    if (!zipValid) return out;
    NSMutableArray<NSDictionary *> *manifests=[NSMutableArray array];
    NSDictionary *main=IPARPlistForEntry(path,mainPlist);
    if (!main) return out;
    NSString *bundle=[main[@"CFBundleIdentifier"] isKindOfClass:NSString.class]?main[@"CFBundleIdentifier"]:@"";
    NSString *version=[main[@"CFBundleShortVersionString"] isKindOfClass:NSString.class]?main[@"CFBundleShortVersionString"]:@"";
    NSString *minIOS=[main[@"MinimumOSVersion"] isKindOfClass:NSString.class]?main[@"MinimumOSVersion"]:@"";
    out[@"bundle"]=bundle;
    out[@"version"]=version;
    out[@"minIOS"]=minIOS.length?minIOS:@"—";
    [manifests addObject:@{@"plist":mainPlist,@"value":main}];
    for (NSString *name in names) {
        if ([name hasSuffix:@".appex/Info.plist"] || [name hasSuffix:@".framework/Info.plist"]) {
            NSDictionary *property=IPARPlistForEntry(path,name);
            if (property) [manifests addObject:@{@"plist":name,@"value":property}];
            if (manifests.count>150) break;
        }
    }
    NSMutableSet<NSString *> *executables=[NSMutableSet set];
    for (NSDictionary *manifest in manifests) {
        NSString *entry=manifest[@"plist"];
        NSDictionary *property=manifest[@"value"];
        NSString *exe=[property[@"CFBundleExecutable"] isKindOfClass:NSString.class]?property[@"CFBundleExecutable"]:nil;
        if (exe.length && [exe isEqualToString:exe.lastPathComponent] && ![exe isEqualToString:@".."]) {
            NSString *dir=entry.stringByDeletingLastPathComponent;
            NSString *target=[dir stringByAppendingPathComponent:exe];
            if (IPARFindFileInZip(names,target)) [executables addObject:target];
        }
    }
    NSUInteger frameworkCount=0,pluginCount=0;
    for (NSString *name in names) {
        if ([name hasSuffix:@".dylib"] && [name hasPrefix:@"Payload/"]) [executables addObject:name];
        if ([name containsString:@".framework/Info.plist"]) frameworkCount++;
        if ([name containsString:@".appex/Info.plist"]) pluginCount++;
    }
    out[@"plugins"]=@(pluginCount);
    out[@"frameworks"]=@(frameworkCount);
    BOOL encrypted=NO,allKnown=YES;
    NSUInteger checked=0;
    if (executables.count==0 || executables.count>120) allKnown=NO;
    for (NSString *entry in executables) {
        if (!allKnown) break;
        NSString *temp=IPARFindTempPath();
        BOOL extracted=IPARUnzipEntry(path,entry,temp);
        BOOL found=NO;
        BOOL ok=extracted && IPARScanMachO(temp,&encrypted,&found);
        [[NSFileManager defaultManager] removeItemAtPath:temp error:nil];
        checked++;
        if (!ok || !found) {allKnown=NO;break;}
    }
    out[@"executables"]=@(checked);
    out[@"drm"]=allKnown?(encrypted?@"encrypted":@"clear"):@"unknown";
    // Lack of encryption is NECESSARY but never SUFFICIENT for TrollStore.
    out[@"troll"]=encrypted?@"blocked":(allKnown?@"unverified":@"unknown");
    return out;
}
@end
''',"utf-8")

# Extend detail page, keep existing actions intact.
p=root/"Controllers/IPARIPADetailViewController.m"
s=p.read_text("utf-8")
a='#import "../Utils/IPARLanguageManager.h"'
assert s.count(a)==1
s=s.replace(a,a+'\n#import "../Utils/IPARIPAAudit.h"\n#import "../Extensions/IPARConstants.h"',1)
a='@property (nonatomic, copy) NSString *bundleIdentifier;'
assert s.count(a)==1
s=s.replace(a,a+'\n@property (nonatomic, strong) NSDictionary *audit;\n@property (nonatomic) BOOL auditing;',1)
a='''    self.tableView.estimatedRowHeight=64;'''
assert s.count(a)==1
s=s.replace(a,a+r'''
    self.auditing=YES;
    NSString *path=[kIPARangerDocumentsPath stringByAppendingPathComponent:self.fileName];
    dispatch_async(dispatch_get_global_queue(QOS_CLASS_UTILITY,0), ^{
        NSDictionary *result=[IPARIPAAudit inspectFileAtPath:path];
        dispatch_async(dispatch_get_main_queue(), ^{
            self.auditing=NO;
            self.audit=result;
            NSString *bundle=result[@"bundle"];
            if ([bundle isKindOfClass:NSString.class] && bundle.length>0)
                self.bundleIdentifier=bundle;
            NSString *version=result[@"version"];
            if ([version isKindOfClass:NSString.class] && version.length>0)
                self.appVersion=version;
            [self.tableView reloadData];
        });
    });''',1)
a='''- (NSInteger)numberOfSectionsInTableView:(UITableView *)tableView { return 3; }'''
assert s.count(a)==1
s=s.replace(a,'- (NSInteger)numberOfSectionsInTableView:(UITableView *)tableView { return 4; }',1)
a='''return section == 0 ? 1 : section == 1 ? 4 : 2;'''
assert s.count(a)==1
s=s.replace(a,'''return section == 0 ? 1 : section == 1 ? 4 : section == 2 ? 2 : 5;''',1)
a='''    if (section==2) return IPARL(@"Actions");
    return nil;'''
assert s.count(a)==1
s=s.replace(a,'''    if (section==2) return IPARL(@"Actions");
    if (section==3) return IPARL(@"IPA integrity and compatibility");
    return nil;''',1)
a='''    if (index.row==0) {
        UIStackView *column = [[UIStackView alloc] init];'''
assert s.count(a)==1
s=s.replace(a,r'''    if (index.section==3) {
        NSArray *keys=@[IPARL(@"ZIP structure"),IPARL(@"SHA-256"),
                       IPARL(@"Minimum iOS"),IPARL(@"FairPlay encryption"),
                       IPARL(@"TrollStore installability")];
        cell.textLabel.text=keys[index.row];
        NSString *value=IPARL(@"Checking…");
        if (self.audit) {
            if (index.row==0) {
                NSString *state=self.audit[@"zip"];
                value=[state isEqualToString:@"valid"]?IPARL(@"Valid"):
                     [state isEqualToString:@"invalid"]?IPARL(@"Invalid"):IPARL(@"Not verified");
            } else if (index.row==1) value=self.audit[@"sha"] ?: @"—";
            else if (index.row==2) value=self.audit[@"minIOS"] ?: @"—";
            else if (index.row==3) {
                NSString *state=self.audit[@"drm"];
                value=[state isEqualToString:@"encrypted"]?IPARL(@"Encrypted (FairPlay)"):
                     [state isEqualToString:@"clear"]?IPARL(@"No Mach-O encryption found"):
                     IPARL(@"Not verified");
            } else {
                NSString *state=self.audit[@"troll"];
                value=[state isEqualToString:@"blocked"]?IPARL(@"Blocked: encrypted binary"):
                      [state isEqualToString:@"unverified"]?IPARL(@"Needs signing/entitlement check"):
                      IPARL(@"Not verified");
            }
        }
        cell.detailTextLabel.text=value;
        cell.detailTextLabel.numberOfLines=0;
        cell.selectionStyle=UITableViewCellSelectionStyleNone;
        return cell;
    }
    if (index.row==0) {
        UIStackView *column = [[UIStackView alloc] init];''',1)
p.write_text(s,"utf-8")
translations={
"IPA integrity and compatibility":"Tính toàn vẹn và khả năng tương thích IPA",
"ZIP structure":"Cấu trúc ZIP",
"SHA-256":"SHA-256",
"Minimum iOS":"iOS tối thiểu",
"FairPlay encryption":"Mã hóa FairPlay",
"TrollStore installability":"Khả năng cài TrollStore",
"Checking…":"Đang kiểm tra…",
"Valid":"Hợp lệ",
"Invalid":"Không hợp lệ",
"Not verified":"Chưa xác minh",
"Encrypted (FairPlay)":"Binary được mã hóa (FairPlay)",
"No Mach-O encryption found":"Không phát hiện mã hóa Mach-O",
"Blocked: encrypted binary":"Không thể cài: binary còn mã hóa",
"Needs signing/entitlement check":"Cần kiểm tra chữ ký và entitlement"
}
for lang,index in (("en",0),("vi",1)):
    p=root/"Resources"/(lang+".lproj")/"Localizable.strings"
    s=p.read_text("utf-8")
    for en,vi in translations.items():
        k=json.dumps(en,ensure_ascii=False)
        if k+" =" not in s: s+=f"{k} = {json.dumps((en,vi)[index],ensure_ascii=False)};\n"
    p.write_text(s,"utf-8")
print("v0.4 audit: ZIP CRC, SHA256, embedded Info.plist, and Mach-O DRM indicators")
