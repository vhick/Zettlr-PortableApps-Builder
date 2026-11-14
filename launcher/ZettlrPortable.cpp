// Zettlr PortableApps community launcher. GPL-3.0-or-later; original implementation.
// Source: https://github.com/Zettlr/Zettlr ; no system-wide registration or elevation.
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <shellapi.h>
#include <tlhelp32.h>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>
#include <cwctype>
#include <system_error>
namespace fs=std::filesystem;

static std::wstring quoted(const std::wstring& s) {
    std::wstring o=L"\""; unsigned slashes=0;
    for (wchar_t c:s) {
        if(c==L'\\'){++slashes;continue;}
        if(c==L'\"'){o.append(slashes*2+1,L'\\');o+=L'\"';slashes=0;continue;}
        o.append(slashes,L'\\');slashes=0;o+=c;
    }
    o.append(slashes*2,L'\\');o+=L'\"';return o;
}
static void error(const std::wstring& msg) { MessageBoxW(nullptr,msg.c_str(),L"Zettlr Portable",MB_OK|MB_ICONERROR); }
static bool hasReparse(const fs::path& p) {
    DWORD a=GetFileAttributesW(p.c_str());return a!=INVALID_FILE_ATTRIBUTES && (a & FILE_ATTRIBUTE_REPARSE_POINT);
}
static bool ensureSafeDir(const fs::path& p) {
    // Prevent a redirected Data or its direct descendants. Fail closed on symlink/junction.
    std::error_code ec;
    if (hasReparse(p)) return false;
    if (!fs::exists(p,ec)) fs::create_directories(p,ec);
    return !ec && fs::is_directory(p,ec) && !hasReparse(p);
}
static void audit(const fs::path& root,const std::wstring& message) {
    std::wofstream out(root / L"Data" / L"TraceGuard" / L"audit.log",std::ios::app);
    if(out){SYSTEMTIME t;GetLocalTime(&t);out <<t.wYear<<L"-"<<t.wMonth<<L"-"<<t.wDay<<L" "<<t.wHour<<L":"<<t.wMinute<<L":"<<t.wSecond<<L" "<<message<<L"\n";}
}
static bool samePath(const std::wstring& a,const std::wstring& b) {
    return CompareStringOrdinal(a.c_str(),-1,b.c_str(),-1,TRUE)==CSTR_EQUAL;
}
static bool processAtPath(const std::wstring& target) {
    HANDLE ss=CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0);
    if(ss==INVALID_HANDLE_VALUE) return true; // Unknown => avoid cleanup
    PROCESSENTRY32W p{};p.dwSize=sizeof(p);
    bool found=false;
    if(Process32FirstW(ss,&p)) do {
        if(_wcsicmp(p.szExeFile,L"Zettlr.exe")!=0)continue;
        HANDLE h=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,FALSE,p.th32ProcessID);
        if(!h){found=true;break;} // Ambiguous => preserve host files
        wchar_t name[32768];DWORD n=32768;
        if(!QueryFullProcessImageNameW(h,0,name,&n) || samePath(name,target)) found=true;
        CloseHandle(h);
        if(found)break;
    }while(Process32NextW(ss,&p));
    CloseHandle(ss);return found;
}
// Conservative coexistence guard: never clean even an empty newly created
// default-profile folder while another Zettlr process may own it.
static bool anyZettlrActive() {
    HANDLE snap=CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS,0);
    if(snap==INVALID_HANDLE_VALUE)return true; // uncertain => keep host state
    PROCESSENTRY32W p{};p.dwSize=sizeof(p);
    bool active=false;
    if(Process32FirstW(snap,&p)) do {
        if(_wcsicmp(p.szExeFile,L"Zettlr.exe")==0){active=true;break;}
    }while(Process32NextW(snap,&p));
    CloseHandle(snap);
    return active;
}
// Only one source-evidenced external trace: empty Roaming\Zettlr\Dictionaries.
// Never touch pre-existing trees, files, symlinks or data with content.
static bool isEmptyRealDirectory(const fs::path& path) {
    std::error_code ec;
    if(hasReparse(path) || !fs::is_directory(path,ec) || ec) return false;
    return fs::directory_iterator(path,ec)==fs::directory_iterator() && !ec;
}
static unsigned long long fnv1a(const std::wstring& s) {
    unsigned long long x=14695981039346656037ULL;
    for(wchar_t c:s){x^=static_cast<unsigned>(std::towlower(c));x*=1099511628211ULL;}return x;
}
int WINAPI wWinMain(HINSTANCE,HINSTANCE,PWSTR,int) {
    wchar_t exeBuffer[32768];DWORD n=GetModuleFileNameW(nullptr,exeBuffer,32768);
    if(n==0 || n>=32767){error(L"Unable to locate launcher directory.");return 2;}
    const fs::path root=fs::path(std::wstring(exeBuffer,n)).parent_path();
    const fs::path target=root/L"App"/L"Zettlr"/L"Zettlr.exe";
    const fs::path data=root/L"Data";
    const fs::path profile=data/L"Profile";
    const fs::path docs=profile/L"PortableDocuments";
    const fs::path trace=data/L"TraceGuard";
    const fs::path recovered=trace/L"Recovered"/L"Roaming"/L"Zettlr"/L"Dictionaries";
    // Static self-test runs BEFORE package assembly; it never modifies Data or the host.
    int argc=0;LPWSTR* argv=CommandLineToArgvW(GetCommandLineW(),&argc);
    if(!argv){error(L"Could not parse command-line arguments.");return 4;}
    if(argc==2 && wcscmp(argv[1],L"--self-test")==0){
        bool ok = (quoted(L"abc def") == L"\"abc def\"") && samePath(L"DATA",L"data");
        LocalFree(argv);return ok ? 0 : 7;
    }
    if(!fs::exists(target) || hasReparse(root) || !ensureSafeDir(data) || !ensureSafeDir(profile) || !ensureSafeDir(docs) || !ensureSafeDir(trace)) {
        LocalFree(argv);error(L"Missing Zettlr.exe or unsafe portable Data location (symlink/junction or permissions). No host settings were modified.");return 3;
    }
    for(int i=1;i<argc;++i){
        // Prevent callers from redirecting our source-backed profile to host storage.
        if(wcsncmp(argv[i],L"--data-dir",10)==0 || wcsncmp(argv[i],L"--user-data-dir",15)==0){
            LocalFree(argv);error(L"Do not supply --data-dir or --user-data-dir to the portable launcher.");return 5;
        }
    }
    std::wstring mutexName=L"Local\\ZettlrPortableCommunity_"+std::to_wstring(fnv1a(root.native()));
    HANDLE mutex=CreateMutexW(nullptr,FALSE,mutexName.c_str());
    bool first=mutex && GetLastError()!=ERROR_ALREADY_EXISTS;
    // Environment query is local to launcher; do not change global APPDATA/TEMP.
    std::wstring appdata;
    DWORD need=GetEnvironmentVariableW(L"APPDATA",nullptr,0);
    if(need>1){std::wstring buffer(need,L'\0');DWORD got=GetEnvironmentVariableW(L"APPDATA",buffer.data(),need);if(got>0 && got<need)appdata.assign(buffer.data(),got);}
    fs::path hostParent=fs::path(appdata)/L"Zettlr";
    fs::path hostDict=hostParent/L"Dictionaries";
    // Snapshot only; never remove any pre-existing host state.
    const bool existedParent=appdata.empty() || fs::exists(hostParent);
    const bool existedDict=appdata.empty() || fs::exists(hostDict);
    std::wstring args=quoted(target.wstring())+L" "+quoted(L"--data-dir="+profile.wstring())+L" "+quoted(L"--user-data-dir="+profile.wstring());
    for(int i=1;i<argc;++i){args+=L" ";args+=quoted(argv[i]);}
    LocalFree(argv);
    // Applies ONLY to this child process and descendants. No OS registration.
    if(!SetEnvironmentVariableW(L"ZETTLR_PORTABLE_MODE",L"1")) {
        audit(root,L"ERROR: unable to configure child-only portable mode; refusing launch.");
        if(mutex)CloseHandle(mutex);
        error(L"Cannot initialize portable environment safely. Zettlr was not started.");
        return 8;
    }
    STARTUPINFOW si{};si.cb=sizeof(si);PROCESS_INFORMATION pi{};
    std::vector<wchar_t> mutableLine(args.begin(),args.end());mutableLine.push_back(L'\0');
    std::wstring working=target.parent_path().wstring();
    if(!CreateProcessW(target.c_str(),mutableLine.data(),nullptr,nullptr,FALSE,0,nullptr,working.c_str(),&si,&pi)){
        DWORD code=GetLastError();audit(root,L"ERROR: app launch failed "+std::to_wstring(code));
        if(mutex)CloseHandle(mutex);error(L"Zettlr process failed to launch; check Data/TraceGuard/audit.log.");return 6;
    }
    CloseHandle(pi.hThread);
    audit(root,L"Started Zettlr with private profile and Documents folder.");
    WaitForSingleObject(pi.hProcess,INFINITE);
    DWORD exitCode=0;GetExitCodeProcess(pi.hProcess,&exitCode);CloseHandle(pi.hProcess);
    // Chromium child processes may outlive main briefly; no cleanup while active.
    if(first){
        bool stillActive=false;
        for(int sec=0;sec<30;++sec){
            if(!processAtPath(target.wstring()))break;
            stillActive=true;Sleep(1000);
        }
        stillActive=processAtPath(target.wstring());
        if(!stillActive && !anyZettlrActive() && !existedDict && !appdata.empty() && isEmptyRealDirectory(hostDict)) {
            // Persist exact empty directory hierarchy before attempting safe removal.
            if(ensureSafeDir(trace/L"Recovered") && ensureSafeDir(trace/L"Recovered"/L"Roaming") &&
               ensureSafeDir(trace/L"Recovered"/L"Roaming"/L"Zettlr") && ensureSafeDir(recovered)) {
                std::error_code ec;fs::remove(hostDict,ec);
                if(!ec){audit(root,L"Recovered new empty Roaming\\Zettlr\\Dictionaries to Data\\TraceGuard.");
                    if(!existedParent && isEmptyRealDirectory(hostParent))fs::remove(hostParent,ec);
                }else audit(root,L"Left host Dictionaries unchanged: removal failed.");
            }
        }else if(!existedDict && fs::exists(hostDict))audit(root,L"Left new host Dictionaries untouched: not empty, active process, or ambiguous.");
    } else audit(root,L"Concurrent launcher: host recovery handled by first launcher.");
    audit(root,L"Zettlr main exited with code "+std::to_wstring(exitCode));
    if(mutex)CloseHandle(mutex);
    return static_cast<int>(exitCode);
}
